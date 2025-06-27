"""
异步任务管理器 - 处理AI会议纪要生成的异步任务
"""

import threading
import time
import uuid
import logging
import json
import os
from typing import Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败


class AsyncTask:
    """异步任务类"""
    
    def __init__(self, task_id: str, task_type: str, task_data: Dict[str, Any]):
        self.task_id = task_id
        self.task_type = task_type
        self.task_data = task_data
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.progress = 0
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress
        }


class AsyncTaskManager:
    """异步任务管理器"""

    def __init__(self, max_workers: int = 2, task_timeout: int = 300, persist_dir: str = "task_data"):
        self.max_workers = max_workers
        self.task_timeout = task_timeout
        self.tasks: Dict[str, AsyncTask] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self.worker_threads = []
        self.running = False
        self.lock = threading.Lock()
        self.persist_dir = persist_dir

        # 创建持久化目录
        os.makedirs(self.persist_dir, exist_ok=True)

        # 加载已存在的任务
        self._load_tasks()
        
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
        logger.info(f"注册任务处理器: {task_type}")
        
    def start(self):
        """启动任务管理器"""
        if self.running:
            return
            
        self.running = True
        
        # 启动工作线程
        for i in range(self.max_workers):
            thread = threading.Thread(target=self._worker_loop, name=f"TaskWorker-{i}")
            thread.daemon = True
            thread.start()
            self.worker_threads.append(thread)
            
        # 启动清理线程
        cleanup_thread = threading.Thread(target=self._cleanup_loop, name="TaskCleanup")
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        logger.info(f"异步任务管理器已启动，工作线程数: {self.max_workers}")
        
    def stop(self):
        """停止任务管理器"""
        self.running = False
        logger.info("异步任务管理器已停止")
        
    def submit_task(self, task_type: str, task_data: Dict[str, Any], task_id: Optional[str] = None) -> str:
        """提交异步任务"""
        if task_id is None:
            task_id = str(uuid.uuid4())
            
        if task_type not in self.task_handlers:
            raise ValueError(f"未注册的任务类型: {task_type}")
            
        task = AsyncTask(task_id, task_type, task_data)

        with self.lock:
            self.tasks[task_id] = task
            self._save_task(task)

        logger.info(f"提交异步任务: {task_id} ({task_type})")
        return task_id
        
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                return task.to_dict()
            return None
            
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """获取任务结果"""
        with self.lock:
            task = self.tasks.get(task_id)
            if task and task.status == TaskStatus.COMPLETED:
                return task.result
            return None
            
    def _worker_loop(self):
        """工作线程循环"""
        while self.running:
            task = self._get_pending_task()
            if task:
                self._execute_task(task)
            else:
                time.sleep(1)  # 没有任务时休眠1秒
                
    def _get_pending_task(self) -> Optional[AsyncTask]:
        """获取待执行的任务"""
        with self.lock:
            for task in self.tasks.values():
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now()
                    self._save_task(task)
                    return task
            return None
            
    def _execute_task(self, task: AsyncTask):
        """执行任务"""
        try:
            logger.info(f"开始执行任务: {task.task_id} ({task.task_type})")

            # 获取任务处理器
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"未找到任务处理器: {task.task_type}")

            # 执行任务
            result = handler(task.task_data, task)

            # 更新任务状态
            with self.lock:
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.now()
                task.progress = 100
                self._save_task(task)

            logger.info(f"任务执行成功: {task.task_id}")

        except Exception as e:
            logger.error(f"任务执行失败: {task.task_id}, 错误: {e}")

            with self.lock:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
                self._save_task(task)
                
    def _cleanup_loop(self):
        """清理过期任务"""
        while self.running:
            try:
                cutoff_time = datetime.now() - timedelta(hours=1)  # 清理1小时前的任务
                
                with self.lock:
                    expired_tasks = [
                        task_id for task_id, task in self.tasks.items()
                        if task.completed_at and task.completed_at < cutoff_time
                    ]
                    
                    for task_id in expired_tasks:
                        del self.tasks[task_id]
                        self._delete_task_file(task_id)

                if expired_tasks:
                    logger.info(f"清理过期任务: {len(expired_tasks)}个")

            except Exception as e:
                logger.error(f"清理任务时出错: {e}")

    def _save_task(self, task: AsyncTask):
        """保存任务到文件"""
        try:
            task_file = os.path.join(self.persist_dir, f"{task.task_id}.json")
            task_data = task.to_dict()
            # 添加任务数据
            task_data['task_data'] = task.task_data

            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务失败 {task.task_id}: {e}")

    def _load_tasks(self):
        """从文件加载任务"""
        try:
            if not os.path.exists(self.persist_dir):
                return

            for filename in os.listdir(self.persist_dir):
                if filename.endswith('.json'):
                    task_file = os.path.join(self.persist_dir, filename)
                    try:
                        with open(task_file, 'r', encoding='utf-8') as f:
                            task_data = json.load(f)

                        # 重建任务对象
                        task = AsyncTask(
                            task_data['task_id'],
                            task_data['task_type'],
                            task_data.get('task_data', {})
                        )
                        task.status = TaskStatus(task_data['status'])
                        task.result = task_data.get('result')
                        task.error = task_data.get('error')
                        task.progress = task_data.get('progress', 0)

                        # 解析时间
                        task.created_at = datetime.fromisoformat(task_data['created_at'])
                        if task_data.get('started_at'):
                            task.started_at = datetime.fromisoformat(task_data['started_at'])
                        if task_data.get('completed_at'):
                            task.completed_at = datetime.fromisoformat(task_data['completed_at'])

                        self.tasks[task.task_id] = task
                        logger.info(f"加载任务: {task.task_id} (状态: {task.status.value})")

                    except Exception as e:
                        logger.error(f"加载任务文件失败 {filename}: {e}")
                        # 删除损坏的文件
                        try:
                            os.remove(task_file)
                        except:
                            pass

        except Exception as e:
            logger.error(f"加载任务失败: {e}")

    def _delete_task_file(self, task_id: str):
        """删除任务文件"""
        try:
            task_file = os.path.join(self.persist_dir, f"{task_id}.json")
            if os.path.exists(task_file):
                os.remove(task_file)
        except Exception as e:
            logger.error(f"删除任务文件失败 {task_id}: {e}")
                
            time.sleep(300)  # 每5分钟清理一次


# 全局任务管理器实例
task_manager = AsyncTaskManager(max_workers=2, task_timeout=300)
