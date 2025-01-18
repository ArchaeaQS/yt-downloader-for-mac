import os
import subprocess
import zipfile
from pathlib import Path

import requests

import config


class ToolManager:
    def __init__(self, save_dir=None):
        """
        macOSでは ~/Library/Application Support/yt-downloader/tools をデフォルト保存先とします。
        """
        if save_dir is None:
            self.save_dir = Path.home() / "Library" / "Application Support" / "yt-downloader" / "tools"
            self.save_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.save_dir = Path(save_dir)

    def _get_tool_path(self, tool_name: str) -> Path:
        """
        ダウンロードしたツールの保存先パスを返す
        """
        return self.save_dir / tool_name

    def check_tool_exists(self, tool_name: str) -> bool:
        """
        ツールが指定パスに存在するか確認
        """
        return self._get_tool_path(tool_name).exists()

    def is_tool_installed(self, tool_name: str) -> bool:
        """
        システムパスまたは同梱パスにツールがインストールされているかを確認
        """
        tool_path = self._get_tool_path(tool_name)  # save_dir 内のツールのパスを取得
        return tool_path.exists() and tool_path.is_file()

    def download_file(self, url: str, save_path: str) -> bool:
        """
        指定URLのファイルをダウンロードし、save_pathに保存する
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # ステータスコード200以外で例外発生
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
            return True
        except requests.RequestException as e:
            print(f"ダウンロードエラー: {e}")
            return False

    def check_and_download_ffmpeg(self) -> bool:
        """
        ffmpegをシステムパスもしくは同梱ツールとして確認し、なければダウンロードして解凍する
        """
        ffmpeg_path = self._get_tool_path("ffmpeg")  # macOSなら拡張子不要
        if self.is_tool_installed("ffmpeg"):
            return True
        if ffmpeg_path.exists():
            # PATHに追加
            os.environ["PATH"] += os.pathsep + str(self.save_dir)
            return True

        # mac向けのバイナリ配布URL例: https://evermeet.cx/ffmpeg/
        # 必要に応じてバージョン、URLを修正してください
        url = config.ffmpeg_url
        zip_path = self._get_tool_path("ffmpeg.zip")

        try:
            # ダウンロード
            if self.download_file(url, str(zip_path)):
                # ZIP解凍: Python標準ライブラリのzipfileを使用
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(self.save_dir)

                # ダウンロードしたパッケージに "ffmpeg" という名前で展開される想定
                extracted_ffmpeg = self.save_dir / "ffmpeg"
                if not extracted_ffmpeg.exists():
                    print("解凍後のffmpegが見つかりませんでした")
                    return False

                # ツールマネージャで使うファイル名とそろえる
                extracted_ffmpeg.rename(ffmpeg_path)

                # 実行権限を付与（念のため）
                ffmpeg_path.chmod(0o755)

                # パスに追加
                os.environ["PATH"] += os.pathsep + str(self.save_dir)
                zip_path.unlink(missing_ok=True)
                return True
        except Exception as e:
            print(f"ffmpegダウンロードまたは解凍中にエラーが発生しました: {e}")
            return False

        return False
    
    def check_and_download_ffprobe(self) -> bool:
        """
        ffprobeをシステムパスもしくは同梱ツールとして確認し、なければダウンロードして解凍する
        """
        ffprobe_path = self._get_tool_path("ffprobe")  # macOSなら拡張子不要
        if self.is_tool_installed("ffprobe"):
            return True
        if ffprobe_path.exists():
            # PATHに追加
            os.environ["PATH"] += os.pathsep + str(self.save_dir)
            return True

        url = config.ffprobe_url
        zip_path = self._get_tool_path("ffprobe.zip")

        try:
            # ダウンロード
            if self.download_file(url, str(zip_path)):
                # ZIP解凍: Python標準ライブラリのzipfileを使用
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(self.save_dir)

                # ダウンロードしたパッケージに "ffprobe" という名前で展開される想定
                extracted_ffprobe = self.save_dir / "ffprobe"
                if not extracted_ffprobe.exists():
                    print("解凍後のffprobeが見つかりませんでした")
                    return False

                # ツールマネージャで使うファイル名とそろえる
                extracted_ffprobe.rename(ffprobe_path)

                # 実行権限を付与（念のため）
                ffprobe_path.chmod(0o755)

                # パスに追加
                os.environ["PATH"] += os.pathsep + str(self.save_dir)
                zip_path.unlink(missing_ok=True)
                return True
        except Exception as e:
            print(f"ffprobeダウンロードまたは解凍中にエラーが発生しました: {e}")
            return False

        return False

    def check_and_download_yt_dlp(self) -> bool:
        """
        yt-dlpを同梱ツールとして確認し、なければダウンロード
        """
        yt_dlp_path = self._get_tool_path("yt-dlp")  # macOSなら拡張子不要

        # システムインストール済みならOK
        if self.is_tool_installed("yt-dlp"):
            return True

        # 保存先にファイルがあるか
        if yt_dlp_path.exists():
            # アップデート試行 (macOSの場合、'-U'で動くかはビルド方法により異なる)
            subprocess.run([str(yt_dlp_path), "-U"], check=False)
            return True

        # macOS向け最新リリース (アーキテクチャに合わせて"_macos"などを選択)
        # https://github.com/yt-dlp/yt-dlp/releases/latest
        url = config.yt_dlp_url
        if self.download_file(url, str(yt_dlp_path)):
            yt_dlp_path.chmod(0o755)
            os.environ["PATH"] += os.pathsep + str(self.save_dir)
            return True

        return False

    def check_and_download_atomicparsley(self) -> bool:
        """
        AtomicParsleyを同梱ツールとして確認し、なければダウンロード
        """

        atomic_path = self._get_tool_path("AtomicParsley")

        # システムインストール済みならOK
        if self.is_tool_installed("AtomicParsley"):
            return True

        if atomic_path.exists():
            os.environ["PATH"] += os.pathsep + str(self.save_dir)
            return True

        url = config.atomicparsley_url
        zip_path = self._get_tool_path("AtomicParsley.zip")

        if self.download_file(url, str(zip_path)):
            try:
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(self.save_dir)
                zip_path.unlink(missing_ok=True)

                # 展開後のファイル名が "AtomicParsley" という名前になるか確認
                # リリースによってはサブディレクトリが生成される場合もあります
                extracted_ap = self.save_dir / "AtomicParsley"
                if extracted_ap.exists():
                    extracted_ap.rename(atomic_path)
                    atomic_path.chmod(0o755)
                    os.environ["PATH"] += os.pathsep + str(self.save_dir)
                    return True
                else:
                    print("解凍後のAtomicParsleyが見つかりませんでした")
                    return False
            except Exception as e:
                print(f"AtomicParsley解凍中にエラーが発生しました: {e}")
                return False

        return False


def main():
    tm = ToolManager()
    print("Checking ffmpeg...")
    if tm.check_and_download_ffmpeg():
        print("ffmpeg OK")
    else:
        print("ffmpeg install failed")
    
    print("Checking ffprobe...")
    if tm.check_and_download_ffprobe():
        print("ffprobe OK")
    else:
        print("ffprobe install failed")

    print("Checking yt-dlp...")
    if tm.check_and_download_yt_dlp():
        print("yt-dlp OK")
    else:
        print("yt-dlp install failed")

    print("Checking AtomicParsley...")
    if tm.check_and_download_atomicparsley():
        print("AtomicParsley OK")
    else:
        print("AtomicParsley install failed")


if __name__ == "__main__":
    main()
