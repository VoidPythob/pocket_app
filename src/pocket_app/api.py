from __future__ import annotations

import asyncio
import os
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp
from PyQt6.QtCore import QCoreApplication, QObject, QThread, Qt, pyqtSignal, pyqtSlot

from pocket_app.config import Config

DEFAULT_BASE_URL = Config.api_base_url

_base_url = os.getenv("POCKET_API_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
_session_cookies: dict[str, str] = {}


class ApiError(Exception):
    def __init__(
        self,
        msg: str,
        *,
        code: int | None = None,
        status: int | None = None,
        data: Any = None,
    ) -> None:
        super().__init__(msg)
        self.code = code
        self.status = status
        self.data = data


class _ApiTaskWorker(QObject):
    finished = pyqtSignal(int, object, object)

    @pyqtSlot(int, object)
    def run_task(self, task_id: int, task_factory: object) -> None:
        result: Any = None
        error: str | None = None
        try:
            if not callable(task_factory):
                raise TypeError("task_factory must be callable")
            result = asyncio.run(task_factory())
        except Exception as exc:
            error = str(exc) or exc.__class__.__name__
        self.finished.emit(task_id, result, error)


class _ApiTaskDispatcher(QObject):
    submit_requested = pyqtSignal(int, object)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: _ApiTaskWorker | None = None
        self._next_task_id = 0
        self._callbacks: dict[
            int,
            tuple[int, Callable[[Any], None], Callable[[str], None] | None],
        ] = {}
        self._receiver_tasks: dict[int, set[int]] = {}
        self._tracked_receivers: set[int] = set()
        self._quit_connected = False

    def submit(
        self,
        receiver: QObject,
        task_factory: Callable[[], Awaitable[Any]],
        on_success: Callable[[Any], None],
        on_failure: Callable[[str], None] | None = None,
    ) -> int:
        self._ensure_started()

        self._next_task_id += 1
        task_id = self._next_task_id
        receiver_id = id(receiver)
        self._callbacks[task_id] = (receiver_id, on_success, on_failure)
        self._receiver_tasks.setdefault(receiver_id, set()).add(task_id)
        if receiver_id not in self._tracked_receivers:
            receiver.destroyed.connect(
                lambda _obj=None, current_id=receiver_id: self._cancel_receiver_tasks(current_id)
            )
            self._tracked_receivers.add(receiver_id)

        self.submit_requested.emit(task_id, task_factory)
        return task_id

    def cancel_receiver(self, receiver: QObject) -> None:
        self._cancel_receiver_tasks(id(receiver))

    def shutdown(self) -> None:
        self._callbacks.clear()
        self._receiver_tasks.clear()
        self._tracked_receivers.clear()
        if self._thread is None:
            return

        thread = self._thread
        worker = self._worker
        self._thread = None
        self._worker = None

        if worker is not None:
            try:
                self.submit_requested.disconnect(worker.run_task)
            except TypeError:
                pass
            try:
                worker.finished.disconnect(self._handle_task_finished)
            except TypeError:
                pass

        thread.quit()
        thread.wait(25000)

    def _ensure_started(self) -> None:
        if self._thread is not None and self._worker is not None:
            return

        thread = QThread(self)
        worker = _ApiTaskWorker()
        worker.moveToThread(thread)
        self.submit_requested.connect(worker.run_task, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(self._handle_task_finished, Qt.ConnectionType.QueuedConnection)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()

        self._thread = thread
        self._worker = worker

        app = QCoreApplication.instance()
        if app is not None and not self._quit_connected:
            app.aboutToQuit.connect(self.shutdown)
            self._quit_connected = True

    def _handle_task_finished(self, task_id: int, data: Any, error: object) -> None:
        callbacks = self._callbacks.pop(task_id, None)
        if callbacks is None:
            return

        receiver_id, on_success, on_failure = callbacks
        task_ids = self._receiver_tasks.get(receiver_id)
        if task_ids is not None:
            task_ids.discard(task_id)
            if not task_ids:
                self._receiver_tasks.pop(receiver_id, None)
                self._tracked_receivers.discard(receiver_id)

        if error:
            if on_failure is not None:
                on_failure(str(error))
            return
        on_success(data)

    def _cancel_receiver_tasks(self, receiver_id: int) -> None:
        task_ids = self._receiver_tasks.pop(receiver_id, set())
        for task_id in task_ids:
            self._callbacks.pop(task_id, None)
        self._tracked_receivers.discard(receiver_id)


_task_dispatcher: _ApiTaskDispatcher | None = None


def _get_task_dispatcher() -> _ApiTaskDispatcher:
    global _task_dispatcher
    if _task_dispatcher is None:
        _task_dispatcher = _ApiTaskDispatcher()
    return _task_dispatcher


def submit_api_task(
    receiver: QObject,
    task_factory: Callable[[], Awaitable[Any]],
    on_success: Callable[[Any], None],
    on_failure: Callable[[str], None] | None = None,
) -> int:
    return _get_task_dispatcher().submit(receiver, task_factory, on_success, on_failure)


def cancel_api_tasks(receiver: QObject) -> None:
    _get_task_dispatcher().cancel_receiver(receiver)


def set_base_url(base_url: str) -> None:
    global _base_url
    _base_url = base_url.rstrip("/")


def get_base_url() -> str:
    return _base_url


def clear_session() -> None:
    _session_cookies.clear()


async def _request_async(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_data: dict[str, Any] | None = None,
) -> Any:
    url = f"{_base_url}{path}"
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.request(
            method,
            url,
            params=_clean_mapping(params),
            json=json_data,
            cookies=_session_cookies or None,
            headers={"Accept": "application/json"},
        ) as response:
            _update_session_cookies(response.cookies)
            payload = await _read_response_payload(response)
            return _unwrap_result(response.status, payload)


async def _read_response_payload(response: aiohttp.ClientResponse) -> Any:
    content_type = response.headers.get("Content-Type", "")
    if "application/json" in content_type:
        return await response.json()
    text = await response.text()
    return {"code": response.status, "msg": text, "data": text}


def _unwrap_result(status: int, payload: Any) -> Any:
    if isinstance(payload, dict) and {"code", "msg"}.issubset(payload.keys()):
        code = payload.get("code")
        msg = payload.get("msg") or "API request failed"
        data = payload.get("data")
        if isinstance(code, int) and code >= 400:
            raise ApiError(msg, code=code, status=status, data=data)
        if status >= 400:
            raise ApiError(msg, code=code, status=status, data=data)
        return data

    if status >= 400:
        raise ApiError("API request failed", status=status, data=payload)
    return payload


def _clean_mapping(mapping: dict[str, Any] | None) -> dict[str, Any] | None:
    if mapping is None:
        return None
    return {key: value for key, value in mapping.items() if value is not None and value != ""}


def _update_session_cookies(cookies: Any) -> None:
    if not cookies:
        return
    for name, morsel in cookies.items():
        value = getattr(morsel, "value", "")
        if value:
            _session_cookies[name] = value
        else:
            _session_cookies.pop(name, None)


async def _get(path: str, *, params: dict[str, Any] | None = None) -> Any:
    return await _request_async("GET", path, params=params)


async def _post(path: str, *, json_data: dict[str, Any] | None = None) -> Any:
    return await _request_async("POST", path, json_data=json_data)


async def _put(path: str, *, json_data: dict[str, Any] | None = None) -> Any:
    return await _request_async("PUT", path, json_data=json_data)


async def _patch(path: str, *, json_data: dict[str, Any] | None = None) -> Any:
    return await _request_async("PATCH", path, json_data=json_data)


async def _delete(path: str) -> Any:
    return await _request_async("DELETE", path)


async def _return_async(value: Any) -> Any:
    return value


def _extract_collection(value: Any, *container_keys: str) -> Any:
    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        return value

    for key in container_keys:
        nested = value.get(key)
        if isinstance(nested, list):
            return nested
        if isinstance(nested, dict):
            extracted = _extract_collection(nested)
            if isinstance(extracted, list):
                return extracted

    for key in ("results", "items", "list", "rows", "records"):
        nested = value.get(key)
        if isinstance(nested, list):
            return nested
    return value


async def admin_login(email: str, password: str) -> Any:
    return await _post(
        "/admin/login/",
        json_data={"email": email, "password": password},
    )


async def admin_register(email: str, password: str, password_confirm: str) -> Any:
    return await _post(
        "/admin/register/",
        json_data={
            "email": email,
            "password": password,
            "password_confirm": password_confirm,
        },
    )


async def list_pets(
    generation_id: int | None = None,
    feature_id: int | None = None,
    name: str = "",
    page: int | None = None,
) -> Any:
    return await _get(
        "/pets/",
        params={
            "generation_id": generation_id,
            "feature_id": feature_id,
            "name": name,
            "page": page,
        },
    )


async def get_pet_detail(pet_id: int) -> Any:
    return await _get(f"/pets/{pet_id}/")


async def get_pet_detail_payload(pet_id: int) -> dict[str, Any]:
    raw_detail = await get_pet_detail(pet_id)
    detail = raw_detail.get("detail") if isinstance(raw_detail, dict) and isinstance(raw_detail.get("detail"), dict) else raw_detail
    if not isinstance(detail, dict):
        return {"detail": {}, "features": [], "capture_methods": []}

    features = _extract_collection(detail.get("features"), "features")
    capture_methods = _extract_collection(detail.get("capture_methods"), "capture_methods")
    need_features = features is None
    need_capture_methods = capture_methods is None

    if need_features or need_capture_methods:
        fallback_results = await asyncio.gather(
            list_pet_features(pet_id, page=1) if need_features else _return_async(features),
            list_pet_capture_methods(pet_id, page=1) if need_capture_methods else _return_async(capture_methods),
            return_exceptions=True,
        )
        if need_features and not isinstance(fallback_results[0], Exception):
            features = _extract_collection(fallback_results[0], "features")
        if need_capture_methods and not isinstance(fallback_results[1], Exception):
            capture_methods = _extract_collection(fallback_results[1], "capture_methods")

    return {
        "detail": detail,
        "features": features if features is not None else [],
        "capture_methods": capture_methods if capture_methods is not None else [],
    }


async def list_pet_features(pet_id: int, page: int | None = None) -> Any:
    return await _get(f"/pets/{pet_id}/features/", params={"page": page})


async def list_pet_capture_methods(pet_id: int, page: int | None = None) -> Any:
    return await _get(f"/pets/{pet_id}/capture_methods/", params={"page": page})


async def get_capture_method_detail(capture_method_id: int) -> Any:
    return await _get(f"/capture_methods/{capture_method_id}/")


async def list_features(name: str = "", page: int | None = None) -> Any:
    return await _get("/features/", params={"name": name, "page": page})


async def get_feature_detail(feature_id: int) -> Any:
    return await _get(f"/features/{feature_id}/")


async def list_skills(name: str = "", page: int | None = None) -> Any:
    return await _get("/skills/", params={"name": name, "page": page})


async def get_skill_detail(skill_id: int) -> Any:
    return await _get(f"/skills/{skill_id}/")


async def list_items(
    category_id: int | None = None,
    name: str = "",
    page: int | None = None,
) -> Any:
    return await _get(
        "/items/",
        params={"category_id": category_id, "name": name, "page": page},
    )


async def get_item_detail(item_id: int) -> Any:
    return await _get(f"/items/{item_id}/")


async def list_egg_groups() -> Any:
    return await _get("/egg-groups/")


async def list_generations(page: int | None = None) -> Any:
    return await _get("/generations/", params={"page": page})


async def get_generation_detail(generation_id: int) -> Any:
    return await _get(f"/generations/{generation_id}/")


async def get_egg_group_detail(egg_group_id: int) -> Any:
    return await _get(f"/egg-groups/{egg_group_id}/")


async def list_egg_group_pets(egg_group_id: int, page: int | None = None) -> Any:
    return await _get(f"/egg-groups/{egg_group_id}/pets/", params={"page": page})


async def list_game_docs(
    group_id: int | None = None,
    page: int | None = None,
) -> Any:
    return await _get("/game-docs/", params={"group_id": group_id, "page": page})


async def get_game_doc_detail(game_doc_id: int) -> Any:
    return await _get(f"/game-docs/{game_doc_id}/")


async def list_game_doc_categories() -> Any:
    return await _get("/game-doc-categories/")


def get_file_url(file_id: str) -> str:
    return f"{get_base_url()}/files/{str(file_id).strip().strip('/')}/"


async def create_admin_pet(
    icon_urls: list[str],
    name: str,
    jp_name: str,
    en_name: str,
    feature_ids: list[int],
    rance_id: int,
    skill_ids: list[int],
) -> Any:
    return await _post(
        "/admin/pets/",
        json_data={
            "icon_urls": icon_urls,
            "name": name,
            "jp_name": jp_name,
            "en_name": en_name,
            "feature_ids": feature_ids,
            "rance_id": rance_id,
            "skill_ids": skill_ids,
        },
    )


async def list_admin_tags() -> Any:
    return await _get("/admin/tags/")


async def create_admin_tag(name: str) -> Any:
    return await _post("/admin/tags/", json_data={"name": name})


async def update_admin_tag(tag_id: int, name: str) -> Any:
    return await _put(f"/admin/tags/{tag_id}/", json_data={"name": name})


async def patch_admin_tag(tag_id: int, **fields: Any) -> Any:
    return await _patch(f"/admin/tags/{tag_id}/", json_data=fields)


async def list_admin_rances() -> Any:
    return await _get("/admin/rances/")


async def get_admin_rance_detail(rance_id: int) -> Any:
    return await _get(f"/admin/rances/{rance_id}/")


async def create_admin_rance(**fields: Any) -> Any:
    return await _post("/admin/rances/", json_data=fields)


async def update_admin_rance(rance_id: int, **fields: Any) -> Any:
    return await _put(f"/admin/rances/{rance_id}/", json_data=fields)


async def patch_admin_rance(rance_id: int, **fields: Any) -> Any:
    return await _patch(f"/admin/rances/{rance_id}/", json_data=fields)


async def delete_admin_rance(rance_id: int) -> Any:
    return await _delete(f"/admin/rances/{rance_id}/")


async def list_admin_features() -> Any:
    return await _get("/admin/features/")


async def get_admin_feature_detail(feature_id: int) -> Any:
    return await _get(f"/admin/features/{feature_id}/")


async def create_admin_feature(introduction: str, detail: str) -> Any:
    return await _post(
        "/admin/features/",
        json_data={"introduction": introduction, "detail": detail},
    )


async def update_admin_feature(feature_id: int, introduction: str, detail: str) -> Any:
    return await _put(
        f"/admin/features/{feature_id}/",
        json_data={"introduction": introduction, "detail": detail},
    )


async def patch_admin_feature(feature_id: int, **fields: Any) -> Any:
    return await _patch(f"/admin/features/{feature_id}/", json_data=fields)


async def delete_admin_feature(feature_id: int) -> Any:
    return await _delete(f"/admin/features/{feature_id}/")


async def list_admin_generations() -> Any:
    return await _get("/admin/generations/")


async def get_admin_generation_detail(generation_id: int) -> Any:
    return await _get(f"/admin/generations/{generation_id}/")


async def create_admin_generation(name: str) -> Any:
    return await _post("/admin/generations/", json_data={"name": name})


async def update_admin_generation(generation_id: int, name: str) -> Any:
    return await _put(f"/admin/generations/{generation_id}/", json_data={"name": name})


async def patch_admin_generation(generation_id: int, **fields: Any) -> Any:
    return await _patch(f"/admin/generations/{generation_id}/", json_data=fields)


async def delete_admin_generation(generation_id: int) -> Any:
    return await _delete(f"/admin/generations/{generation_id}/")


async def list_admin_skills() -> Any:
    return await _get("/admin/skills/")


async def get_admin_skill_detail(skill_id: int) -> Any:
    return await _get(f"/admin/skills/{skill_id}/")


async def create_admin_skill(**fields: Any) -> Any:
    return await _post("/admin/skills/", json_data=fields)


async def update_admin_skill(skill_id: int, **fields: Any) -> Any:
    return await _put(f"/admin/skills/{skill_id}/", json_data=fields)


async def patch_admin_skill(skill_id: int, **fields: Any) -> Any:
    return await _patch(f"/admin/skills/{skill_id}/", json_data=fields)


async def delete_admin_skill(skill_id: int) -> Any:
    return await _delete(f"/admin/skills/{skill_id}/")


async def list_admin_skill_categories() -> Any:
    return await _get("/admin/skill-categories/")


async def get_admin_skill_category_detail(category_id: int) -> Any:
    return await _get(f"/admin/skill-categories/{category_id}/")


async def create_admin_skill_category(name: str) -> Any:
    return await _post("/admin/skill-categories/", json_data={"name": name})


async def update_admin_skill_category(category_id: int, name: str) -> Any:
    return await _put(f"/admin/skill-categories/{category_id}/", json_data={"name": name})


async def patch_admin_skill_category(category_id: int, **fields: Any) -> Any:
    return await _patch(f"/admin/skill-categories/{category_id}/", json_data=fields)


async def delete_admin_skill_category(category_id: int) -> Any:
    return await _delete(f"/admin/skill-categories/{category_id}/")


async def list_admin_items() -> Any:
    return await _get("/admin/items/")


async def get_admin_item_detail(item_id: int) -> Any:
    return await _get(f"/admin/items/{item_id}/")


async def create_admin_item(**fields: Any) -> Any:
    return await _post("/admin/items/", json_data=fields)


async def update_admin_item(item_id: int, **fields: Any) -> Any:
    return await _put(f"/admin/items/{item_id}/", json_data=fields)


async def patch_admin_item(item_id: int, **fields: Any) -> Any:
    return await _patch(f"/admin/items/{item_id}/", json_data=fields)


async def delete_admin_item(item_id: int) -> Any:
    return await _delete(f"/admin/items/{item_id}/")


async def list_admin_item_categories() -> Any:
    return await _get("/admin/item-categories/")


async def get_admin_item_category_detail(category_id: int) -> Any:
    return await _get(f"/admin/item-categories/{category_id}/")


async def create_admin_item_category(name: str) -> Any:
    return await _post("/admin/item-categories/", json_data={"name": name})


async def update_admin_item_category(category_id: int, name: str) -> Any:
    return await _put(f"/admin/item-categories/{category_id}/", json_data={"name": name})


async def patch_admin_item_category(category_id: int, **fields: Any) -> Any:
    return await _patch(f"/admin/item-categories/{category_id}/", json_data=fields)


async def delete_admin_item_category(category_id: int) -> Any:
    return await _delete(f"/admin/item-categories/{category_id}/")


async def list_admin_egg_groups() -> Any:
    return await _get("/admin/egg-groups/")


async def get_admin_egg_group_detail(egg_group_id: int) -> Any:
    return await _get(f"/admin/egg-groups/{egg_group_id}/")


async def create_admin_egg_group(name: str) -> Any:
    return await _post("/admin/egg-groups/", json_data={"name": name})


async def update_admin_egg_group(egg_group_id: int, name: str) -> Any:
    return await _put(f"/admin/egg-groups/{egg_group_id}/", json_data={"name": name})


async def patch_admin_egg_group(egg_group_id: int, **fields: Any) -> Any:
    return await _patch(f"/admin/egg-groups/{egg_group_id}/", json_data=fields)


async def delete_admin_egg_group(egg_group_id: int) -> Any:
    return await _delete(f"/admin/egg-groups/{egg_group_id}/")


async def list_admin_game_docs() -> Any:
    return await _get("/admin/game-docs/")


async def get_admin_game_doc_detail(game_doc_id: int) -> Any:
    return await _get(f"/admin/game-docs/{game_doc_id}/")


async def create_admin_game_doc(**fields: Any) -> Any:
    return await _post("/admin/game-docs/", json_data=fields)


async def update_admin_game_doc(game_doc_id: int, **fields: Any) -> Any:
    return await _put(f"/admin/game-docs/{game_doc_id}/", json_data=fields)


async def patch_admin_game_doc(game_doc_id: int, **fields: Any) -> Any:
    return await _patch(f"/admin/game-docs/{game_doc_id}/", json_data=fields)


async def delete_admin_game_doc(game_doc_id: int) -> Any:
    return await _delete(f"/admin/game-docs/{game_doc_id}/")


async def list_admin_pet_rances(pet_id: int) -> Any:
    return await _get(f"/admin/pets/{pet_id}/rances/")


async def create_admin_pet_rance_binding(pet_id: int, rance_id: int) -> Any:
    return await _post(
        f"/admin/pets/{pet_id}/rances/",
        json_data={"rance_id": rance_id},
    )


async def update_admin_pet_rance_binding(
    pet_id: int,
    rance_id: int,
    new_rance_id: int,
) -> Any:
    return await _put(
        f"/admin/pets/{pet_id}/rances/{rance_id}/",
        json_data={"new_rance_id": new_rance_id},
    )


async def delete_admin_pet_rance_binding(pet_id: int, rance_id: int) -> Any:
    return await _delete(f"/admin/pets/{pet_id}/rances/{rance_id}/")


async def list_admin_pet_egg_groups(pet_id: int) -> Any:
    return await _get(f"/admin/pets/{pet_id}/egg-groups/")


async def create_admin_pet_egg_group_binding(pet_id: int, egg_group_id: int) -> Any:
    return await _post(
        f"/admin/pets/{pet_id}/egg-groups/",
        json_data={"egg_group_id": egg_group_id},
    )


async def update_admin_pet_egg_group_binding(
    pet_id: int,
    egg_group_id: int,
    new_egg_group_id: int,
) -> Any:
    return await _put(
        f"/admin/pets/{pet_id}/egg-groups/{egg_group_id}/",
        json_data={"new_egg_group_id": new_egg_group_id},
    )


async def delete_admin_pet_egg_group_binding(pet_id: int, egg_group_id: int) -> Any:
    return await _delete(f"/admin/pets/{pet_id}/egg-groups/{egg_group_id}/")


async def list_admin_pet_generations(pet_id: int) -> Any:
    return await _get(f"/admin/pets/{pet_id}/generations/")


async def create_admin_pet_generation_binding(pet_id: int, generation_id: int) -> Any:
    return await _post(
        f"/admin/pets/{pet_id}/generations/",
        json_data={"generation_id": generation_id},
    )


async def update_admin_pet_generation_binding(
    pet_id: int,
    generation_id: int,
    new_generation_id: int,
) -> Any:
    return await _put(
        f"/admin/pets/{pet_id}/generations/{generation_id}/",
        json_data={"new_generation_id": new_generation_id},
    )


async def delete_admin_pet_generation_binding(pet_id: int, generation_id: int) -> Any:
    return await _delete(f"/admin/pets/{pet_id}/generations/{generation_id}/")
