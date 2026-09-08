# Third-party software

The NEON application source is MIT licensed. This does not replace the licenses of its dependencies.

| Component | Upstream | License |
| --- | --- | --- |
| yt-dlp | https://github.com/yt-dlp/yt-dlp | Unlicense (Python distribution) |
| yt-dlp-ejs | https://github.com/yt-dlp/ejs | Unlicense; bundled MIT/ISC components |
| CustomTkinter | https://github.com/TomSchimansky/CustomTkinter | MIT |
| Python | https://www.python.org | PSF license and included third-party notices |
| PyInstaller | https://pyinstaller.org | GPL with bootloader exception |
| Node.js | https://github.com/nodejs/node | MIT and bundled third-party notices |
| imageio-ffmpeg | https://github.com/imageio/imageio-ffmpeg | BSD; FFmpeg executable has separate terms |

Package license files are preserved under `licenses`. Exact Python dependency versions are in `requirements.txt`.
FFmpeg is distributed as a separate, unmodified executable within the application bundle and is invoked as a subprocess.
Its version, build configuration and licensing are recorded in `licenses/FFmpeg-version.txt` and `licenses/FFmpeg-license.txt`.
The bundled FFmpeg is 7.1 essentials by Gyan, licensed under GPL v3 or later. Binary supplier and build/source references: https://github.com/imageio/imageio-ffmpeg and https://www.gyan.dev/ffmpeg/builds/ . FFmpeg source: https://github.com/FFmpeg/FFmpeg/tree/n7.1 .
Consult the FFmpeg build license before redistributing a modified package.
