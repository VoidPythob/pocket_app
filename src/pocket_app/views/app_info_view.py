from __future__ import annotations

from pocket_app import __version__
from pocket_app.resources import tr

from .view_helpers import (
    BasePageView,
    clear_layout,
    make_metric_card,
    make_section_title,
)


class AppInfoView(BasePageView):
    page_title_key = "page.app_info.title"
    page_description_key = "page.app_info.description"
    search_placeholder_key = "page.app_info.search"

    async def fetch_data(self):
        return {"version": __version__}

    def render_data(self, data) -> None:
        clear_layout(self.content_layout)

        version = __version__
        if isinstance(data, dict):
            raw_version = data.get("version")
            if raw_version is not None:
                version = str(raw_version)

        panel, layout = self.build_panel("pageCard")
        layout.addWidget(make_section_title(tr("app_info.section"), panel))
        layout.addWidget(
            make_metric_card(
                tr("app_info.version"),
                version,
                tr("app_info.version_desc"),
                panel,
            )
        )

        self.content_layout.addWidget(panel)
        self.content_layout.addStretch(1)
