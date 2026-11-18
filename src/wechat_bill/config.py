from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DeviceConfig(BaseModel):
    serial: str = ""
    adb_host: str = "127.0.0.1"
    adb_port: int = 5037


class OCRConfig(BaseModel):
    engine: str = "rapid"  # rapid | paddle | umi
    lang: str = "ch"


class ParseConfig(BaseModel):
    list_top_ratio: float = 0.18
    edge_bottom_px: int = 24
    amount_y_tolerance: float = 80.0
    income_keywords: List[str] = Field(
        default_factory=lambda: ["退款", "收款", "入账", "红包", "工资", "来自"]
    )


class CollectConfig(BaseModel):
    max_scrolls: int = 100
    scroll_duration_ms: int = 350
    wait_after_scroll: float = 1.2
    no_new_threshold: int = 2


class OutputConfig(BaseModel):
    dir: str = "output"
    save_screenshots: bool = False


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WBO_",
        env_nested_delimiter="__",
        extra="ignore",
    )

    device: DeviceConfig = Field(default_factory=DeviceConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)
    parse: ParseConfig = Field(default_factory=ParseConfig)
    collect: CollectConfig = Field(default_factory=CollectConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @classmethod
    def load(cls, config_path: Optional[str | Path] = None) -> "Settings":
        """从 TOML 文件加载配置，不存在则用默认值。"""
        path = Path(config_path or "config.toml")
        if not path.exists():
            # 也尝试 config.example.toml 旁边的默认位置
            example = Path("config.example.toml")
            if example.exists():
                path = example
            else:
                return cls()

        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib  # type: ignore

        with open(path, "rb") as f:
            data = tomllib.load(f)

        return cls.model_validate(data)
