#!/usr/bin/env python3
"""
系统配置管理器
负责管理系统配置的读取、保存和验证
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """系统配置管理器"""
    
    def __init__(self, config_file: str = None):
        # 如果在Docker环境中，使用config目录
        if config_file is None:
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "system_config.json"

        self.config_file = Path(config_file)
        self.config_data = {}
        self.default_config = self._get_default_config()
        self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置 - 初始化为空，需要用户手动配置"""
        return {
            "ai": {
                "ark_api_key": "",
                "ark_model": "ep-20250618123643-dtts7",  # 保留模型名作为默认值
                "ark_base_url": "https://ark.cn-beijing.volces.com/api/v3",  # 保留API地址作为默认值
                "ark_timeout": 300
            },
            "storage": {
                "tos_access_key": "",
                "tos_secret_key": "",
                "tos_bucket": "",
                "tos_region": "cn-beijing",  # 保留默认区域
                "tos_endpoint": "tos-cn-beijing.volces.com",  # 保留默认端点
                "max_file_size": 500
            },
            "asr": {
                "asr_app_key": "",
                "asr_access_key": "",
                "asr_model": "bigmodel",  # 保留默认模型
                "asr_timeout": 1800
            },
            "prompt": {
                "system_prompt": """你是一个专业的会议纪要生成助手。请根据提供的会议录音转录内容，生成规范的会议纪要。

要求：
1. 提取会议的关键信息和决策要点
2. 整理发言人的主要观点和建议
3. 突出重要的行动项和后续安排
4. 使用专业、简洁的语言
5. 保持客观中性的表述
6. 将口语化表达转换为书面语
7. 根据提供的航空术语词汇表，将相关术语规范化

请按照以下格式生成会议纪要：

# 会议纪要

**会议名称：** {meeting_name}
**会议时间：** {meeting_time}
**会议地点：** {meeting_location}
**参会人员：** {attendees}

## 会议议题

## 主要内容

## 重要决策

## 行动事项

## 后续安排

请确保内容准确、完整、专业。""",
                "glossary": """塔台 - 控制塔
跑道 - 起降跑道
航班 - 航班号
机长 - 飞行员
副驾驶 - 副飞行员
空管 - 空中交通管制
起飞 - 起飞离港
降落 - 着陆进港
滑行 - 地面滑行
停机坪 - 机坪
廊桥 - 登机桥
候机楼 - 航站楼"""
            },
            "system": {
                "worker_threads": 2,
                "log_level": "INFO",
                "minutes_template": """# {meeting_name}

**时间：** {meeting_time}
**地点：** {meeting_location}
**参会人员：** {attendees}

## 会议内容

{content}

## 决策事项

## 行动计划

---
*本纪要由AI自动生成，请核实内容准确性*"""
            }
        }
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # 合并加载的配置和默认配置，确保结构完整
                self.config_data = self._merge_config(self.default_config, loaded_config)
                logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                # 如果配置文件不存在，使用空的默认配置（需要用户手动配置）
                self.config_data = self.default_config.copy()
                logger.info("配置文件不存在，使用默认空配置，请通过系统设置配置相关参数")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.config_data = self.default_config.copy()

    def _merge_config(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置和加载的配置"""
        result = default.copy()
        for section, values in loaded.items():
            if section in result and isinstance(values, dict):
                result[section].update(values)
            else:
                result[section] = values
        return result
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            logger.info(f"配置文件保存成功: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get_config(self, section: Optional[str] = None) -> Dict[str, Any]:
        """获取配置"""
        if section:
            return self.config_data.get(section, {})
        return self.config_data
    
    def update_config(self, section: str, config: Dict[str, Any]) -> bool:
        """更新配置"""
        try:
            if section not in self.config_data:
                self.config_data[section] = {}
            
            self.config_data[section].update(config)
            return self.save_config()
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return False
    
    def reset_config(self, section: Optional[str] = None) -> bool:
        """重置配置为默认值"""
        try:
            if section:
                if section in self.default_config:
                    self.config_data[section] = self.default_config[section].copy()
            else:
                self.config_data = self.default_config.copy()
            
            return self.save_config()
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            return False
    
    def validate_config(self, section: str, config: Dict[str, Any]) -> tuple[bool, str]:
        """验证配置的有效性"""
        try:
            if section == "ai":
                required_fields = ["ark_api_key", "ark_model", "ark_base_url"]
                for field in required_fields:
                    if not config.get(field):
                        return False, f"AI配置缺少必填字段: {field}"
                
                if config.get("ark_timeout", 0) < 30:
                    return False, "AI超时时间不能少于30秒"
            
            elif section == "storage":
                required_fields = ["tos_access_key", "tos_secret_key", "tos_bucket"]
                for field in required_fields:
                    if not config.get(field):
                        return False, f"存储配置缺少必填字段: {field}"
                
                if config.get("max_file_size", 0) < 1:
                    return False, "最大文件大小不能少于1MB"
            
            elif section == "asr":
                required_fields = ["asr_app_key", "asr_access_key"]
                for field in required_fields:
                    if not config.get(field):
                        return False, f"ASR配置缺少必填字段: {field}"
            
            elif section == "system":
                worker_threads = config.get("worker_threads", 1)
                if not isinstance(worker_threads, int) or worker_threads < 1:
                    return False, "工作线程数必须是大于0的整数"
            
            return True, "配置验证通过"
        
        except Exception as e:
            return False, f"配置验证失败: {str(e)}"
    
    def is_configured(self) -> Dict[str, bool]:
        """检查各个模块是否已配置"""
        status = {}

        # 检查AI配置
        ai_config = self.get_config("ai")
        status["ai"] = bool(ai_config.get("ark_api_key"))

        # 检查存储配置
        storage_config = self.get_config("storage")
        status["storage"] = bool(
            storage_config.get("tos_access_key") and
            storage_config.get("tos_secret_key") and
            storage_config.get("tos_bucket")
        )

        # 检查ASR配置
        asr_config = self.get_config("asr")
        status["asr"] = bool(
            asr_config.get("asr_app_key") and
            asr_config.get("asr_access_key")
        )

        # 检查提示词配置
        prompt_config = self.get_config("prompt")
        status["prompt"] = bool(prompt_config.get("system_prompt"))

        return status

    def get_missing_configs(self) -> list[str]:
        """获取缺失的配置项"""
        status = self.is_configured()
        missing = []

        config_names = {
            "ai": "豆包AI配置",
            "storage": "TOS存储配置",
            "asr": "语音识别配置",
            "prompt": "提示词配置"
        }

        for key, configured in status.items():
            if not configured:
                missing.append(config_names.get(key, key))

        return missing

# 全局配置管理器实例
config_manager = ConfigManager()
