from fastapi import APIRouter, HTTPException
from core.app_config import AppConfig
from api.models import SettingsResponse, UpdateMusicLibraryRequest

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("", response_model=SettingsResponse)
def get_settings():
    path = AppConfig.get_music_library_root()
    source = AppConfig.get_config_source("music_library_root")
    
    # Map unknown to default to satisfy strict literal
    if source not in ("db", "env", "default"):
        source = "default"
        
    return SettingsResponse(
        music_library_path=str(path),
        source=source # type: ignore
    )

@router.put("/music-library-path", response_model=SettingsResponse)
def update_music_library_path(payload: UpdateMusicLibraryRequest):
    try:
        AppConfig.set_music_library_root(payload.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return get_settings()
