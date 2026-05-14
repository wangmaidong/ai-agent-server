from app.batis.batis_utils.batis_scheme import BatisModuleConfig

DEMO_MODULE_CONFIG = BatisModuleConfig.to_obj({
  "tableName": "pl_demo",
  "base": "/pl_demo",
  "columns": {
    "id": {"valueType": "string"},
    "createdAt": {"valueType": "datetime"},
    "createdBy": {"valueType": "string"},
    "updatedAt": {"valueType": "datetime"},
    "updatedBy": {"valueType": "string"},
    "count": {"valueType": "number"},
    "normalText": {"valueType": "string"},
    "numberVal": {"valueType": "number"},
    "createdFullName": {
      "valueType": "string",
      "query": "t2.full_name",
    },
  },
  "joinConfig": [
    {
      "type": "left join",
      "table": "pl_user",
      "alia": "t2",
      "on": "t1.created_by = t2.id"
    },
  ]
})
