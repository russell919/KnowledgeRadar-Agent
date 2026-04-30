"""
Bitable Service - 多维表格服务

处理多维表格数据的解析和查询
"""

from typing import List, Dict, Any, Optional


class BitableService:
    """
    多维表格服务
    
    提供多维表格数据的解析和查询功能
    """
    
    def __init__(self, feishu_client):
        self.feishu_client = feishu_client
    
    async def get_table_records(
        self,
        table_id: str,
        view_id: Optional[str] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取表格记录
        
        Args:
            table_id: 表格ID
            view_id: 视图ID
            filter_conditions: 过滤条件
        
        Returns:
            记录列表
        """
        table_data = await self.feishu_client.read_bitable(table_id, view_id)
        records = table_data.get("records", [])
        
        if filter_conditions:
            records = self._filter_records(records, filter_conditions)
        
        return records
    
    def _filter_records(
        self,
        records: List[Dict[str, Any]],
        conditions: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        过滤记录
        
        Args:
            records: 记录列表
            conditions: 过滤条件
        
        Returns:
            过滤后的记录列表
        """
        filtered = []
        
        for record in records:
            fields = record.get("fields", {})
            match = True
            
            for key, value in conditions.items():
                if fields.get(key) != value:
                    match = False
                    break
            
            if match:
                filtered.append(record)
        
        return filtered
    
    def get_column_names(self, table_id: str) -> List[str]:
        """
        获取列名列表（需要实际调用飞书API）
        
        Args:
            table_id: 表格ID
        
        Returns:
            列名列表
        """
        # TODO: 需要调用飞书API获取表格结构
        return []
    
    def aggregate_records(
        self,
        records: List[Dict[str, Any]],
        group_by: str,
        aggregations: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        聚合记录
        
        Args:
            records: 记录列表
            group_by: 分组字段
            aggregations: 聚合操作，如 {"count": "COUNT", "sum": "SUM"}
        
        Returns:
            聚合结果
        """
        result = {}
        
        for record in records:
            fields = record.get("fields", {})
            key = fields.get(group_by, "unknown")
            
            if key not in result:
                result[key] = {}
            
            for agg_key, agg_type in aggregations.items():
                value = fields.get(agg_key)
                
                if agg_type == "COUNT":
                    result[key][agg_key] = result[key].get(agg_key, 0) + 1
                elif agg_type == "SUM":
                    result[key][agg_key] = result[key].get(agg_key, 0) + (value or 0)
                elif agg_type == "MAX":
                    current = result[key].get(agg_key, float("-inf"))
                    result[key][agg_key] = max(current, value or float("-inf"))
                elif agg_type == "MIN":
                    current = result[key].get(agg_key, float("inf"))
                    result[key][agg_key] = min(current, value or float("inf"))
        
        return result
