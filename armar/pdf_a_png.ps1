# Pasa las páginas de un PDF a PNG con el lector de PDF que trae Windows
# (Windows.Data.Pdf), sin instalar nada: en esta laptop no hay pdftoppm,
# Ghostscript ni ImageMagick. Sirve para mirar la hoja imprimible y el PDF de
# respaldo de la charla.
#
# Uso (Windows PowerShell 5.1):
#   powershell -NoProfile -ExecutionPolicy Bypass -File armar\pdf_a_png.ps1 <archivo.pdf> <carpeta_salida> [ancho_px]
# Deja pagina_01.png, pagina_02.png, ... Ojo: Windows multiplica el ancho pedido
# por la escala de pantalla (125 % en esta laptop): 1275 px pedidos salen 1594.

param(
    [Parameter(Mandatory = $true)][string]$Pdf,
    [Parameter(Mandatory = $true)][string]$Salida,
    [int]$Ancho = 1700
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFolder, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
$null = [Windows.Data.Pdf.PdfPageRenderOptions, Windows.Data.Pdf, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapEncoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]

$metodos = [System.WindowsRuntimeSystemExtensions].GetMethods()
$comoTarea = $metodos | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
$comoTareaAccion = $metodos | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' } | Select-Object -First 1

function Esperar($operacion, [Type]$tipo) {
    $tarea = $comoTarea.MakeGenericMethod($tipo).Invoke($null, @($operacion))
    $null = $tarea.Wait(-1)
    return $tarea.Result
}
function EsperarAccion($accion) {
    $tarea = $comoTareaAccion.Invoke($null, @($accion))
    $null = $tarea.Wait(-1)
}

$rutaPdf = (Resolve-Path $Pdf).Path
$null = New-Item -ItemType Directory -Force -Path $Salida
$rutaSalida = (Resolve-Path $Salida).Path

$archivo = Esperar ([Windows.Storage.StorageFile]::GetFileFromPathAsync($rutaPdf)) ([Windows.Storage.StorageFile])
$documento = Esperar ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($archivo)) ([Windows.Data.Pdf.PdfDocument])
$carpeta = Esperar ([Windows.Storage.StorageFolder]::GetFolderFromPathAsync($rutaSalida)) ([Windows.Storage.StorageFolder])

for ($i = 0; $i -lt $documento.PageCount; $i++) {
    $pagina = $documento.GetPage($i)
    $nombre = "pagina_{0:D2}.png" -f ($i + 1)
    $destino = Esperar ($carpeta.CreateFileAsync($nombre, [Windows.Storage.CreationCollisionOption]::ReplaceExisting)) ([Windows.Storage.StorageFile])
    $flujo = Esperar ($destino.OpenAsync([Windows.Storage.FileAccessMode]::ReadWrite)) ([Windows.Storage.Streams.IRandomAccessStream])
    $opciones = New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $opciones.DestinationWidth = [uint32]$Ancho
    $opciones.BitmapEncoderId = [Windows.Graphics.Imaging.BitmapEncoder]::PngEncoderId
    EsperarAccion ($pagina.RenderToStreamAsync($flujo, $opciones))
    $flujo.Dispose()
    $pagina.Dispose()
    Write-Output (Join-Path $rutaSalida $nombre)
}
Write-Output ("Paginas: " + $documento.PageCount)
