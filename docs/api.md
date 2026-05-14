# Pocket API 接口文档

本文档基于当前代码实现整理，接口定义以 [urls.py](/D:/code/web/pocket/pocket_api/src/pocket_api/config/urls.py:1) 为准。

## 1. 基础说明

- 默认端口：`8080`
- 鉴权方式：`SessionAuthentication`
- 管理员接口：需要管理员登录后的会话 Cookie
- 公共接口：当前宠物、技能、物品、蛋组、特性、游戏文档、文件获取相关接口对普通用户开放

## 2. 统一返回

统一返回使用 `Result` 对象，结构定义见 [result.py](/D:/code/web/pocket/pocket_api/src/pocket_api/result.py:1)。

```json
{
  "code": 200,
  "msg": "操作成功",
  "data": {}
}
```

## 3. 登录与权限

### 3.1 管理员登录

- 方法：`POST`
- 路径：`/admin/login/`
- 权限：公开

请求体：

```json
{
  "email": "admin@example.com",
  "password": "123456"
}
```

### 3.2 管理员注册

- 方法：`POST`
- 路径：`/admin/register/`
- 权限：管理员

请求体：

```json
{
  "email": "new-admin@example.com",
  "password": "123456",
  "password_confirm": "123456"
}
```

说明：

- `POST /admin/register/` 仅允许已登录管理员调用，用于注册新的管理员账号

### 3.3 管理员登出

- 方法：`POST`
- 路径：`/admin/logout/`
- 权限：管理员

说明：

- 调用后会清除当前管理员登录会话

## 4. 公共查询接口

### 4.1 宠物列表

- 方法：`GET`
- 路径：`/pets/`
- 权限：公开查询

请求参数：

- `generation_id`：世代 ID，必传
- `feature_id`：特性 ID，可选
- `tag_id`：标签 ID，可选
- `name`：宠物中文名，模糊搜索，可选
- `page_size`：每页条数，可选，最大 `100`
- `page`：页码，可选

说明：

- 只返回指定世代下的宠物
- 支持按特性与世代同时筛选
- 支持按标签与世代同时筛选
- 支持按中文名模糊搜索
- 分页返回包含：`count`、`total_pages`、`next`、`previous`、`results`
- 列表项返回：`id`、`name`、`jp_name`、`en_name`、`first_image_url`、`tags`、`features`
- `tags` 单项包含：`id`、`name`、`color`

### 4.2 宠物详情

- 方法：`GET`
- 路径：`/pets/{id}/`
- 权限：公开查询

说明：

- 返回宠物基础信息、图片、标签、蛋组、特性、种族值、招式列表等完整详情
- `tags` 单项包含：`id`、`name`、`color`

### 4.3 宠物特性列表

- 方法：`GET`
- 路径：`/pets/{id}/features/`
- 权限：公开查询

请求参数：

- `page`：页码，可选

说明：

- `features` 字段为分页结构，包含 `count`、`next`、`previous`、`results`

### 4.4 特性列表

- 方法：`GET`
- 路径：`/features/`
- 权限：公开查询

请求参数：

- `name`：特性名称模糊搜索，可选
- `page`：页码，可选

说明：

- 按当前表结构，`name` 实际匹配 `introduction`

### 4.5 特性详情

- 方法：`GET`
- 路径：`/features/{id}/`
- 权限：公开查询

### 4.6 宠物捕获方式列表

- 方法：`GET`
- 路径：`/pets/{id}/capture_methods/`
- 权限：公开查询

请求参数：

- `page`：页码，可选

说明：

- `capture_methods` 字段为分页结构，包含 `count`、`next`、`previous`、`results`

### 4.7 捕获方式详情

- 方法：`GET`
- 路径：`/capture_methods/{id}/`
- 权限：公开查询

### 4.8 物品列表

- 方法：`GET`
- 路径：`/items/`
- 权限：公开查询

请求参数：

- `category_id`：物品分类 ID，可选
- `name`：物品中文名，模糊搜索，可选
- `page`：页码，可选

说明：

- 支持按物品分类筛选
- 支持按物品中文名模糊搜索
- 列表项返回：`id`、`name`、`jp_name`、`en_name`、`introduction`、`detail`、`categories`

### 4.9 物品详情

- 方法：`GET`
- 路径：`/items/{id}/`
- 权限：公开查询

### 4.10 技能列表

- 方法：`GET`
- 路径：`/skills/`
- 权限：公开查询

请求参数：

- `page`：页码，可选

说明：

- 列表项返回：`id`、`learn_type`、`category_id`、`attribute_id`、`name`、`introduction`、`detail`、`damage`、`aim`、`pp`、`cost_time`

### 4.11 技能详情

- 方法：`GET`
- 路径：`/skills/{id}/`
- 权限：公开查询

### 4.12 蛋组列表

- 方法：`GET`
- 路径：`/egg-groups/`
- 权限：公开查询

### 4.13 世代列表

- 方法：`GET`
- 路径：`/generations/`
- 权限：公开查询

请求参数：

- `page`：页码，可选

### 4.14 世代详情

- 方法：`GET`
- 路径：`/generations/{id}/`
- 权限：公开查询

### 4.15 蛋组详情

- 方法：`GET`
- 路径：`/egg-groups/{id}/`
- 权限：公开查询

### 4.16 根据蛋组反查宠物列表

- 方法：`GET`
- 路径：`/egg-groups/{id}/pets/`
- 权限：公开查询

说明：

- 返回结构包含 `egg_group` 信息以及分页后的宠物列表
- 宠物列表单项结构与 `GET /pets/` 一致

### 4.17 游戏图鉴列表

- 方法：`GET`
- 路径：`/game-docs/`
- 权限：公开查询

请求参数：

- `group_id`：文档组 ID，可选
- `page`：页码，可选

说明：

- 仅返回二级子文档，不返回文档组
- `group_id` 传入后，只返回该文档组下的子文档
- 列表项返回：`id`、`p_id`、`name`、`path`

### 4.18 文档分类列表

- 方法：`GET`
- 路径：`/game-doc-categories/`
- 权限：公开查询

说明：

- 返回所有文档组以及每个组下面的子文档目录
- 仅支持两级结构：文档组 -> 子文档

### 4.19 游戏图鉴详情

- 方法：`GET`
- 路径：`/game-docs/{id}/`
- 权限：公开查询

说明：

- 仅支持查询二级子文档详情
- 详情返回 markdown 内容字段 `content`

### 4.20 文件获取

- 方法：`GET`
- 路径：`/files/{file_id}/`
- 权限：公开查询

说明：

- 根据上传接口返回的 `file_id` 直接获取文件内容
- 该接口返回文件流，不使用 `Result` JSON 包装
- 文件不存在时返回 `404`

### 4.21 标签列表

- 方法：`GET`
- 路径：`/tags/`
- 权限：公开查询

请求参数：

- `page`：页码，可选
- `page_size`：每页条数，可选，最大 `100`

说明：

- 分页返回包含：`count`、`total_pages`、`next`、`previous`、`results`
- 列表项返回：`id`、`name`、`color`

### 4.22 标签详情

- 方法：`GET`
- 路径：`/tags/{id}/`
- 权限：公开查询

## 5. 管理员宠物相关接口

### 5.1 创建宠物

- 方法：`POST`
- 路径：`/admin/pets/`
- 权限：管理员

请求体：

```json
{
  "icon_urls": [
    "https://example.com/pets/1-cover.png",
    "https://example.com/pets/1-detail.png"
  ],
  "name": "皮卡丘",
  "jp_name": "ピカチュウ",
  "en_name": "Pikachu",
  "feature_ids": [1, 2],
  "generation_id": 1,
  "rance_id": 3,
  "skill_ids": [10, 11],
  "tag_ids": [1, 3]
}
```

### 5.1.1 修改宠物

- 方法：`GET` `PUT` `PATCH`
- 路径：`/admin/pets/{id}/`
- 权限：管理员

请求体：

- `PUT`：参数与创建宠物一致，需完整提交
- `PATCH`：按需传入要修改的字段

说明：

- 支持修改 `icon_urls`、`name`、`jp_name`、`en_name`、`feature_ids`、`generation_id`、`rance_id`、`skill_ids`、`tag_ids`
- 传入 `icon_urls` 时会整体替换当前宠物图片，第一张仍作为封面
- 传入 `feature_ids`、`generation_id`、`rance_id`、`skill_ids`、`tag_ids` 时会替换对应关联

说明：

- `icon_urls`、`feature_ids`、`skill_ids`、`tag_ids` 会自动去重
- `generation_id` 为必传
- 第一个图片会作为封面
- 会校验特性、种族、技能、标签是否存在

### 5.2 宠物种族绑定

- `GET /admin/pets/{pet_id}/rances/`：查看当前绑定
- `POST /admin/pets/{pet_id}/rances/`：新增绑定
- `PUT /admin/pets/{pet_id}/rances/{rance_id}/`：替换绑定
- `DELETE /admin/pets/{pet_id}/rances/{rance_id}/`：解除绑定

请求体：

- 新增：`{"rance_id": 3}`
- 替换：`{"new_rance_id": 4}`

### 5.3 宠物蛋组绑定

- `GET /admin/pets/{pet_id}/egg-groups/`
- `POST /admin/pets/{pet_id}/egg-groups/`
- `PUT /admin/pets/{pet_id}/egg-groups/{egg_group_id}/`
- `DELETE /admin/pets/{pet_id}/egg-groups/{egg_group_id}/`

请求体：

- 新增：`{"egg_group_id": 2}`
- 替换：`{"new_egg_group_id": 3}`

### 5.4 宠物世代绑定

- `GET /admin/pets/{pet_id}/generations/`
- `POST /admin/pets/{pet_id}/generations/`
- `PUT /admin/pets/{pet_id}/generations/{generation_id}/`
- `DELETE /admin/pets/{pet_id}/generations/{generation_id}/`

请求体：

- 新增：`{"generation_id": 1}`
- 替换：`{"new_generation_id": 2}`

## 6. 管理员分类与基础资料接口

### 6.1 标签

- `GET /admin/tags/`
- `POST /admin/tags/`
- `PUT /admin/tags/{id}/`
- `PATCH /admin/tags/{id}/`
- `DELETE /admin/tags/{id}/`

字段：

- `name`
- `color`
- 如果标签已经绑定宠物，则不允许删除

### 6.2 种族

- `GET /admin/rances/`
- `GET /admin/rances/{id}/`
- `POST /admin/rances/`
- `PUT /admin/rances/{id}/`
- `PATCH /admin/rances/{id}/`
- `DELETE /admin/rances/{id}/`

说明：

- 列表接口 `GET /admin/rances/` 支持 `page`、`page_size` 分页参数，`page_size` 最大 `100`
- 分页返回包含：`count`、`total_pages`、`next`、`previous`、`results`

字段：

- `p_id`
- `name`
- `hp`
- `attack`
- `defense`
- `special_attack`
- `special_defense`
- `speed`
- `total`

说明：

- 删除为软删除
- 如果已被宠物关联，不允许删除

### 6.3 特性

- `GET /admin/features/`
- `GET /admin/features/{id}/`
- `POST /admin/features/`
- `PUT /admin/features/{id}/`
- `PATCH /admin/features/{id}/`
- `DELETE /admin/features/{id}/`

字段：

- `introduction`
- `detail`

说明：

- 如果已被宠物关联，不允许删除

### 6.4 世代

- `GET /admin/generations/`
- `GET /admin/generations/{id}/`
- `POST /admin/generations/`
- `PUT /admin/generations/{id}/`
- `PATCH /admin/generations/{id}/`
- `DELETE /admin/generations/{id}/`

说明：

- 列表接口 `GET /admin/generations/` 支持 `page`、`page_size` 分页参数，`page_size` 最大 `100`
- 分页返回包含：`count`、`total_pages`、`next`、`previous`、`results`

字段：

- `name`

说明：

- 如果已被宠物关联，不允许删除

### 6.5 技能

- `GET /admin/skills/`
- `GET /admin/skills/{id}/`
- `POST /admin/skills/`
- `PUT /admin/skills/{id}/`
- `PATCH /admin/skills/{id}/`
- `DELETE /admin/skills/{id}/`

说明：

- 列表接口 `GET /admin/skills/` 支持 `page`、`page_size` 分页参数，`page_size` 最大 `100`
- 分页返回包含：`count`、`total_pages`、`next`、`previous`、`results`

字段：

- `learn_type`
- `category_id`
- `attribute_id`
- `name`
- `introduction`
- `detail`
- `damage`
- `aim`
- `pp`
- `cost_time`

说明：

- 如果已被宠物、技能属性、技能影响配置关联，不允许删除

### 6.6 技能分类

- `GET /admin/skill-categories/`
- `GET /admin/skill-categories/{id}/`
- `POST /admin/skill-categories/`
- `PUT /admin/skill-categories/{id}/`
- `PATCH /admin/skill-categories/{id}/`
- `DELETE /admin/skill-categories/{id}/`

字段：

- `name`

说明：

- 如果已被技能使用，不允许删除

### 6.7 物品

- `GET /admin/items/`
- `GET /admin/items/{id}/`
- `POST /admin/items/`
- `PUT /admin/items/{id}/`
- `PATCH /admin/items/{id}/`
- `DELETE /admin/items/{id}/`

字段：

- `name`
- `jp_name`
- `en_name`
- `introduction`
- `detail`

说明：

- 如果已被物品分类关联，不允许删除

### 6.8 物品分类

- `GET /admin/item-categories/`
- `GET /admin/item-categories/{id}/`
- `POST /admin/item-categories/`
- `PUT /admin/item-categories/{id}/`
- `PATCH /admin/item-categories/{id}/`
- `DELETE /admin/item-categories/{id}/`

字段：

- `name`

说明：

- 如果已被物品关联，不允许删除

### 6.9 蛋组

- `GET /admin/egg-groups/`
- `GET /admin/egg-groups/{id}/`
- `POST /admin/egg-groups/`
- `PUT /admin/egg-groups/{id}/`
- `PATCH /admin/egg-groups/{id}/`
- `DELETE /admin/egg-groups/{id}/`

说明：

- 列表接口 `GET /admin/egg-groups/` 支持 `page`、`page_size` 分页参数，`page_size` 最大 `100`
- 分页返回包含：`count`、`total_pages`、`next`、`previous`、`results`

字段：

- `name`

说明：

- 如果已被宠物关联，不允许删除

### 6.10 游戏文档

- `GET /admin/game-docs/`
- `GET /admin/game-docs/{id}/`
- `POST /admin/game-docs/`
- `PUT /admin/game-docs/{id}/`
- `PATCH /admin/game-docs/{id}/`
- `DELETE /admin/game-docs/{id}/`

字段：

- `p_id`
- `name`
- `path`
- `content`

说明：

- 仅支持两级结构：`p_id` 为空表示文档组，`p_id` 有值表示该组下的子文档
- 文档组自身不存正文内容，创建或修改文档组时 `content` 会被清空
- 子文档必须挂在顶级文档组下，且 `content` 必填，内容为 markdown 文本
- 删除文档组前，必须先删除其下全部子文档

### 6.11 文件上传

- 方法：`POST`
- 路径：`/admin/files/`
- 权限：管理员

请求方式：

- `multipart/form-data`
- 字段：`file`

返回示例：

```json
{
  "code": 201,
  "msg": "上传成功",
  "data": {
    "file_id": "9f3d7f8a7df24b65b2960a26a53b6f4a",
    "file_name": "cover.png",
    "content_type": "image/png",
    "size": 10240,
    "url": "/files/9f3d7f8a7df24b65b2960a26a53b6f4a/"
  }
}
```

说明：

- `file_id` 为服务端随机生成
- 获取文件时使用 `GET /files/{file_id}/`
- 不修改数据库表结构，文件元数据保存在服务端文件目录

## 7. 接口总览

### 7.1 公开接口

- `GET /pets/`
- `GET /pets/{id}/`
- `GET /pets/{id}/features/`
- `GET /features/`
- `GET /features/{id}/`
- `GET /pets/{id}/capture_methods/`
- `GET /capture_methods/{id}/`
- `GET /items/`
- `GET /items/{id}/`
- `GET /generations/`
- `GET /generations/{id}/`
- `GET /tags/`
- `GET /tags/{id}/`
- `GET /egg-groups/`
- `GET /egg-groups/{id}/`
- `GET /egg-groups/{id}/pets/`
- `GET /game-docs/`
- `GET /game-docs/{id}/`
- `GET /game-doc-categories/`
- `GET /files/{file_id}/`

### 7.2 管理员接口

- `POST /admin/login/`
- `POST /admin/logout/`
- `POST /admin/register/`
- `POST /admin/pets/import-csv/`
- `POST /admin/pets/`
- `GET|PUT|PATCH|DELETE /admin/pets/{id}/`
- `GET|POST|PUT|PATCH|DELETE /admin/tags/ /admin/tags/{id}/`
- `GET|POST|PUT|PATCH|DELETE /admin/rances/ /admin/rances/{id}/`
- `GET|POST|PUT|PATCH|DELETE /admin/features/ /admin/features/{id}/`
- `GET|POST|PUT|PATCH|DELETE /admin/generations/ /admin/generations/{id}/`
- `GET|POST|PUT|PATCH|DELETE /admin/skills/ /admin/skills/{id}/`
- `GET|POST|PUT|PATCH|DELETE /admin/skill-categories/ /admin/skill-categories/{id}/`
- `GET|POST|PUT|PATCH|DELETE /admin/items/ /admin/items/{id}/`
- `GET|POST|PUT|PATCH|DELETE /admin/item-categories/ /admin/item-categories/{id}/`
- `GET|POST|PUT|PATCH|DELETE /admin/egg-groups/ /admin/egg-groups/{id}/`
- `GET|POST|PUT|PATCH|DELETE /admin/game-docs/ /admin/game-docs/{id}/`
- `POST /admin/files/`
- `GET|POST|PUT|DELETE /admin/pets/{pet_id}/rances/`
- `GET|POST|PUT|DELETE /admin/pets/{pet_id}/egg-groups/`
- `GET|POST|PUT|DELETE /admin/pets/{pet_id}/generations/`

## 8. 常见错误响应

### 8.1 未登录或无权限

```json
{
  "code": 403,
  "msg": "You do not have permission to perform this action.",
  "data": {
    "detail": "You do not have permission to perform this action."
  }
}
```

### 8.2 参数校验失败

```json
{
  "code": 400,
  "msg": "参数校验失败",
  "data": {}
}
```

### 8.3 资源冲突

```json
{
  "code": 409,
  "msg": "资源冲突"
}
```
