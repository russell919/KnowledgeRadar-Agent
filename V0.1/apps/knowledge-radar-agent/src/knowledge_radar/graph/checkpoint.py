"""
Checkpoint Manager - 检查点管理器

管理 Agent 状态的持久化和恢复
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid


@dataclass
class Checkpoint:
    """
    检查点
    """
    checkpoint_id: str
    run_id: str
    state: Dict[str, Any]
    node_name: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class CheckpointManager:
    """
    检查点管理器
    
    将 state 存入 agent_checkpoints
    支持 run_id 查询
    支持 preview 后恢复
    """
    
    def __init__(self):
        self._checkpoints: Dict[str, Checkpoint] = {}
        self._run_checkpoints: Dict[str, List[str]] = {}
    
    async def save_checkpoint(
        self,
        run_id: str,
        state: Dict[str, Any],
        node_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        保存检查点
        
        Args:
            run_id: 运行ID
            state: 状态
            node_name: 节点名称
            metadata: 元数据
        
        Returns:
            checkpoint_id
        """
        checkpoint_id = str(uuid.uuid4())
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            run_id=run_id,
            state=state,
            node_name=node_name,
            metadata=metadata or {},
        )
        
        self._checkpoints[checkpoint_id] = checkpoint
        
        if run_id not in self._run_checkpoints:
            self._run_checkpoints[run_id] = []
        self._run_checkpoints[run_id].append(checkpoint_id)
        
        return checkpoint_id
    
    async def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        获取检查点
        
        Args:
            checkpoint_id: 检查点ID
        
        Returns:
            Checkpoint 或 None
        """
        return self._checkpoints.get(checkpoint_id)
    
    async def get_latest_checkpoint(self, run_id: str) -> Optional[Checkpoint]:
        """
        获取最新的检查点
        
        Args:
            run_id: 运行ID
        
        Returns:
            最新的 Checkpoint 或 None
        """
        checkpoint_ids = self._run_checkpoints.get(run_id, [])
        
        if not checkpoint_ids:
            return None
        
        latest_id = checkpoint_ids[-1]
        return self._checkpoints.get(latest_id)
    
    async def get_all_checkpoints(self, run_id: str) -> List[Checkpoint]:
        """
        获取运行的所有检查点
        
        Args:
            run_id: 运行ID
        
        Returns:
            检查点列表
        """
        checkpoint_ids = self._run_checkpoints.get(run_id, [])
        return [self._checkpoints[cid] for cid in checkpoint_ids if cid in self._checkpoints]
    
    async def restore_from_checkpoint(
        self,
        checkpoint_id: str,
    ) -> Dict[str, Any]:
        """
        从检查点恢复状态
        
        Args:
            checkpoint_id: 检查点ID
        
        Returns:
            恢复的状态
        """
        checkpoint = self._checkpoints.get(checkpoint_id)
        
        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")
        
        return checkpoint.state
    
    async def restore_to_latest(self, run_id: str) -> Dict[str, Any]:
        """
        恢复到最新检查点
        
        Args:
            run_id: 运行ID
        
        Returns:
            恢复的状态
        """
        checkpoint = await self.get_latest_checkpoint(run_id)
        
        if not checkpoint:
            raise ValueError(f"No checkpoints found for run: {run_id}")
        
        return checkpoint.state
    
    async def list_runs(self) -> List[str]:
        """
        列出所有运行ID
        
        Returns:
            运行ID列表
        """
        return list(self._run_checkpoints.keys())
    
    async def delete_run(self, run_id: str) -> bool:
        """
        删除运行的检查点
        
        Args:
            run_id: 运行ID
        
        Returns:
            是否成功
        """
        if run_id not in self._run_checkpoints:
            return False
        
        checkpoint_ids = self._run_checkpoints[run_id]
        
        for cid in checkpoint_ids:
            if cid in self._checkpoints:
                del self._checkpoints[cid]
        
        del self._run_checkpoints[run_id]
        
        return True


# 全局检查点管理器实例
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """
    获取检查点管理器实例
    
    Returns:
        CheckpointManager
    """
    global _checkpoint_manager
    
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    
    return _checkpoint_manager
