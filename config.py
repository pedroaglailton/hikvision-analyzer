# hikvision_analyzer/config.py

EXPECTED_CONFIGS = {
    '101': {
        "Codec": "H.265", "Resolução": "1920×1080", "FPS": "15.0", "GOP": "20",
        "Tipo de Bitrate": "VBR", "Bitrate (Kbps)": "1024", "Qualidade (%)": "60",
        "Bitrate Máx (Kbps)": "1024"
    },
    '102': {
        "Codec": "H.264", "Resolução": "704×480", "FPS": "15.0", "GOP": "15",
        "Tipo de Bitrate": "VBR", "Bitrate (Kbps)": "1024", "Qualidade (%)": "60",
        "Bitrate Máx (Kbps)": "1024"
    },
    '103': {
        "Codec": "H.265", "Resolução": "1280×720", "FPS": "25.0", "GOP": "25",
        "Tipo de Bitrate": "VBR", "Bitrate (Kbps)": "2048", "Qualidade (%)": "60",
        "Bitrate Máx (Kbps)": "2048"
    }
}