# hikvision_analyzer/analyzer.py

from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import time
import concurrent.futures
import pandas as pd
from .utils import get_device_info, capture_snapshot
from .config import EXPECTED_CONFIGS
import requests
import xml.etree.ElementTree as ET
import base64
import io


def get_camera_video_settings(ip, username, password, port=80, timeout=5):
    """Obtém configurações de vídeo da câmera Hikvision via ISAPI."""
    try:
        url = f"http://{ip}:{port}/ISAPI/Streaming/channels"
        auth = HTTPDigestAuth(username, password)
        response = requests.get(url, auth=auth, timeout=timeout, verify=False)

        if response.status_code != 200:
            auth = HTTPBasicAuth(username, password)
            response = requests.get(url, auth=auth, timeout=timeout, verify=False)

        if response.status_code == 200:
            return parse_video_settings(response.content, ip)
        else:
            return []
    except Exception as e:
        print(f"Erro ao obter configurações de vídeo para {ip}: {str(e)}")
        return []


def parse_video_settings(xml_content, ip):
    """Analisa o XML de resposta e extrai informações dos canais de vídeo."""
    try:
        xml_str = xml_content.decode('utf-8', errors='ignore').replace(
            'xmlns="http://www.hikvision.com/ver20/XMLSchema"', ''
        )
        root = ET.fromstring(xml_str)
        channels = []

        for channel in root.findall('.//StreamingChannel'):
            video = channel.find('Video')
            ch_data = {
                "IP": ip,
                "Canal ID": channel.findtext('id', default="N/A"),
                "Nome do Canal": channel.findtext('channelName', default="N/A"),
                "Habilitado": channel.findtext('enabled', default="N/A")
            }

            if video is not None:
                max_frame_rate = video.findtext('maxFrameRate', default="N/A")
                fps = f"{int(max_frame_rate) / 100:.1f}" if max_frame_rate.isdigit() else "N/A"

                ch_data.update({
                    "Codec": video.findtext('videoCodecType', default="N/A"),
                    "Resolução": f"{video.findtext('videoResolutionWidth', default='?')}×{video.findtext('videoResolutionHeight', default='?')}",
                    "FPS": fps,
                    "GOP": video.findtext('GovLength', default="N/A"),
                    "Tipo de Bitrate": video.findtext('videoQualityControlType', default="N/A"),
                    "Bitrate (Kbps)": video.findtext('constantBitRate', default="N/A"),
                    "Qualidade (%)": video.findtext('fixedQuality', default="N/A"),
                    "Bitrate Máx (Kbps)": video.findtext('vbrUpperCap', default="N/A"),
                })
            else:
                ch_data.update({k: "N/A" for k in [
                    "Codec", "Resolução", "FPS", "GOP",
                    "Tipo de Bitrate", "Bitrate (Kbps)",
                    "Qualidade (%)", "Bitrate Máx (Kbps)"
                ]})
            channels.append(ch_data)
        return channels
    except Exception as e:
        print(f"Erro ao processar XML para {ip}: {str(e)}")
        return []


def verificar_config(row):
    """Verifica se a configuração do canal está conforme padrão esperado."""
    canal_id = str(row['Canal ID'])
    if canal_id not in EXPECTED_CONFIGS:
        return "Canal não esperado"
    expected = EXPECTED_CONFIGS[canal_id]
    for key in expected:
        if str(row[key]) != str(expected[key]):
            return "Config. precisa ser corrigida"
    return "Ok - Config. correta"


def detalhar_erros(row):
    """Gera mensagem detalhada com campos incorretos."""
    canal_id = str(row['Canal ID'])
    if canal_id not in EXPECTED_CONFIGS:
        return '<span style="color:red">Canal não esperado</span>'
    expected = EXPECTED_CONFIGS[canal_id]
    erros = []
    for key in expected:
        valor_atual = str(row[key])
        valor_esperado = str(expected[key])
        if valor_atual != valor_esperado:
            erros.append(f'<span style="color:red">{key}: {valor_atual} (esperado: {valor_esperado})</span>')
    return " | ".join(erros) if erros else ""


def process_camera(ip, username, password, port, timeout):
    """Processa uma câmera individual e retorna dados dos canais de vídeo."""
    start_time = time.time()
    device_name = get_device_info(ip, username, password, port, timeout)
    video_settings = get_camera_video_settings(ip, username, password, port, timeout)

    if not video_settings:
        return [{
            "IP": ip,
            "deviceName": device_name,
            "Status": "Erro",
            "Detalhes": "Falha ao obter configurações",
            "Tempo": f"{time.time() - start_time:.2f}s"
        }]

    thumbnail = capture_snapshot(ip, username, password, port, timeout)
    thumbnail_base64 = ""
    if thumbnail:
        buf = io.BytesIO()
        thumbnail.save(buf, format="JPEG", quality=85)
        thumbnail_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    results = []
    for i, channel in enumerate(video_settings):
        channel_data = channel.copy()
        channel_data["IP"] = ip
        channel_data["deviceName"] = device_name
        channel_data["Status"] = "Sucesso"
        channel_data["Tempo"] = f"{time.time() - start_time:.2f}s"
        channel_data["Thumbnail"] = thumbnail_base64 if i == 0 else ""
        results.append(channel_data)
    return results


def analyze_cameras(ips, username, passwords, port=80, timeout=5):
    """Processa múltiplas câmeras em paralelo e retorna um DataFrame com os resultados."""
    results = []
    completed_ips = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        for ip in ips:
            for password in passwords:
                future = executor.submit(process_camera, ip, username, password, port, timeout)
                futures[future] = ip

        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            if ip in completed_ips:
                continue

            try:
                result = future.result()
                if isinstance(result, list):  # Sucesso!
                    results.extend(result)
                    completed_ips.add(ip)
            except Exception as e:
                print(f"Erro ao processar {ip}: {str(e)}")

    df_final = pd.DataFrame(results)

    # Aplica análise somente se tiver dados válidos
    if not df_final.empty and 'Canal ID' in df_final.columns:
        df_valid = df_final[df_final['Canal ID'] != 'N/A'].copy()
        df_invalid = df_final[df_final['Canal ID'] == 'N/A'].copy()

        df_valid["Status da Configuração"] = df_valid.apply(verificar_config, axis=1)
        df_valid["Detalhes da Configuração"] = df_valid.apply(detalhar_erros, axis=1)
    else:
        df_valid = pd.DataFrame()
        df_invalid = df_final.copy()
        print("⚠️ Nenhum dado válido encontrado para análise de configuração.")

    df_final = pd.concat([df_valid, df_invalid], ignore_index=True)
    return df_final