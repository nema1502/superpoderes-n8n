# Abre un .pptx en PowerPoint por COM (sin ventana) y revisa que este sano:
# cuantas diapositivas tiene, las notas del orador, cada video (si arranca al
# entrar, si se rebobina, si se oculta), si la presentacion muestra controles
# multimedia, y exporta cada diapositiva a PNG. Deja un informe JSON en UTF-8.
#
# Con -ProbarShow ademas corre la presentacion EN UNA VENTANA CHICA (320x180 pt,
# arriba a la izquierda, unos 5 s por diapositiva) y le pregunta al reproductor
# de PowerPoint (SlideShowView.Player) en que milisegundo va cada video: asi se
# sabe si arranco solo y si al final quedo en el ultimo cuadro, sin mirar la
# pantalla. No corre si el usuario tiene PowerPoint abierto.
#
# Cuidados (reglas del proyecto):
# - Si el usuario ya tenia PowerPoint abierto, COM se engancha a ESE proceso:
#   entonces solo se cierra la presentacion abierta aca, nunca Quit().
# - El trabajo COM corre en un proceso hijo: al terminar, Windows libera todas
#   sus referencias y PowerPoint puede cerrarse solo despues de Quit(). (Con
#   todo en un mismo proceso, PowerPoint quedaba vivo: medido el 22-oct-2026.)
#   Si aun asi queda vivo, se cierra SOLO el PID que abrio este script.
# - DisplayAlerts se pone en "ninguna" para que un aviso no cuelgue la llamada,
#   y se restaura al final.
#
# Uso (Windows PowerShell 5.1):
#   powershell -NoProfile -ExecutionPolicy Bypass -File armar\verificar_pptx.ps1 -Pptx <archivo.pptx> -Salida <carpeta> [-ProbarShow] [-GuardarCopia <copia.pptx>]
# -GuardarCopia guarda una copia escrita por el propio PowerPoint (SaveCopyAs),
# para ver como reescribe el XML.
# -Exportar "1,34,66" exporta solo esas diapositivas a PNG (por defecto, todas).
# -ProbarHasta N corre la presentacion en ventana solo hasta la diapositiva N.
# El informe incluye las secciones (nombre, primera diapositiva, cantidad).

param(
    [Parameter(Mandatory = $true)][string]$Pptx,
    [Parameter(Mandatory = $true)][string]$Salida,
    [string]$GuardarCopia = "",
    [string]$Exportar = "",
    [int]$ProbarHasta = 0,
    [switch]$ProbarShow,
    [switch]$Interno,
    [switch]$NoCerrarApp
)

$ErrorActionPreference = "Stop"
$ruta = (Resolve-Path $Pptx).Path
$null = New-Item -ItemType Directory -Force -Path $Salida
$carpeta = (Resolve-Path $Salida).Path
$archivoInforme = Join-Path $carpeta "informe.json"

# ------------------------------------------------------------------ padre
if (-not $Interno) {
    $inicio = Get-Date
    $antes = @(Get-Process -Name POWERPNT -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
    $yaAbierto = $antes.Count -gt 0
    $argumentos = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PSCommandPath, "-Pptx", $ruta, "-Salida", $carpeta, "-Interno")
    if ($GuardarCopia -ne "") { $argumentos += @("-GuardarCopia", [System.IO.Path]::GetFullPath($GuardarCopia)) }
    if ($Exportar -ne "") { $argumentos += @("-Exportar", $Exportar) }
    if ($ProbarHasta -gt 0) { $argumentos += @("-ProbarHasta", $ProbarHasta) }
    if ($yaAbierto) { $argumentos += "-NoCerrarApp" }
    if ($ProbarShow -and -not $yaAbierto) { $argumentos += "-ProbarShow" }
    & powershell.exe @argumentos
    $cerrado = $null
    if (-not $yaAbierto) {
        $nuevos = @(Get-Process -Name POWERPNT -ErrorAction SilentlyContinue | Where-Object { $antes -notcontains $_.Id })
        foreach ($p in $nuevos) {
            if (-not $p.WaitForExit(20000)) { Stop-Process -Id $p.Id -Force; $cerrado = $p.Id }
        }
    }
    $informe = Get-Content -Raw -Encoding UTF8 $archivoInforme | ConvertFrom-Json
    $informe | Add-Member -NotePropertyName powerpoint_ya_abierto -NotePropertyValue $yaAbierto
    $informe | Add-Member -NotePropertyName show_probado -NotePropertyValue ([bool]($ProbarShow -and -not $yaAbierto))
    $informe | Add-Member -NotePropertyName powerpoint_cerrado_por_pid -NotePropertyValue $cerrado
    $informe | Add-Member -NotePropertyName powerpoint_despues -NotePropertyValue @(Get-Process -Name POWERPNT -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
    $informe | Add-Member -NotePropertyName total_seg -NotePropertyValue ([math]::Round(((Get-Date) - $inicio).TotalSeconds, 2))
    $json = $informe | ConvertTo-Json -Depth 6
    $json | Out-File -FilePath $archivoInforme -Encoding utf8
    Write-Output $json
    exit 0
}

# ------------------------------------------------------------------ hijo (COM)
function Revisar($app) {
    $informe = [ordered]@{ archivo = $ruta; version_powerpoint = $app.Version }
    $t0 = Get-Date
    # Open(FileName, ReadOnly, Untitled, WithWindow): solo lectura y sin ventana
    $pres = $app.Presentations.Open($ruta, -1, 0, 0)
    try {
        $informe.abrir_seg = [math]::Round(((Get-Date) - $t0).TotalSeconds, 2)
        $informe.nombre = $pres.Name
        $informe.reparada = ($pres.Name -match "repar") -or ($pres.FullName -match "repar")
        $informe.diapositivas = $pres.Slides.Count
        $informe.ancho_pt = $pres.PageSetup.SlideWidth
        $informe.alto_pt = $pres.PageSetup.SlideHeight
        $informe.mostrar_controles_multimedia = $pres.SlideShowSettings.ShowMediaControls  # -1 si, 0 no
        $secciones = @()
        for ($k = 1; $k -le $pres.SectionProperties.Count; $k++) {
            $secciones += [ordered]@{ nombre = $pres.SectionProperties.Name($k); primera = $pres.SectionProperties.FirstSlide($k); cantidad = $pres.SectionProperties.SlidesCount($k) }
        }
        $informe.secciones = $secciones
        # (PowerShell no distingue mayusculas en las variables: $listaExportar, no $exportar, que pisaria el parametro)
        $listaExportar = @()
        if ($Exportar -ne "") { $listaExportar = @($Exportar -split "[,; ]+" | Where-Object { $_ -ne "" } | ForEach-Object { [int]$_ }) }

        $diapos = @()
        for ($i = 1; $i -le $pres.Slides.Count; $i++) {
            $s = $pres.Slides.Item($i)
            $sec = $s.TimeLine.MainSequence
            $efectos = @()
            for ($k = 1; $k -le $sec.Count; $k++) {
                $e = $sec.Item($k)
                $efectos += ("tipo {0}, disparo {1}" -f $e.EffectType, $e.Timing.TriggerType)  # 83 = reproducir medio; disparo 1 clic, 2 con la anterior, 3 despues de la anterior
            }
            $d = [ordered]@{ numero = $i; efectos_secuencia_principal = $efectos }
            $notas = ""
            foreach ($sh in $s.NotesPage.Shapes) {
                if ($sh.Type -eq 14 -and $sh.PlaceholderFormat.Type -eq 2) { $notas = $sh.TextFrame.TextRange.Text }
            }
            $d.notas = $notas
            $medios = @()
            foreach ($sh in $s.Shapes) {
                if ($sh.Type -eq 16) {
                    $ps = $sh.AnimationSettings.PlaySettings
                    $medios += [ordered]@{
                        nombre = $sh.Name; id = $sh.Id
                        tipo_medio = $sh.MediaType  # 3 = video
                        izq = $sh.Left; arriba = $sh.Top; ancho = $sh.Width; alto = $sh.Height
                        duracion_ms = $sh.MediaFormat.Length
                        vinculado = $sh.MediaFormat.IsLinked
                        reproducir_al_entrar = $ps.PlayOnEntry          # -1 = si
                        ocultar_si_no_reproduce = $ps.HideWhileNotPlaying
                        rebobinar_al_terminar = $ps.RewindMovie
                        repetir = $ps.LoopUntilStopped
                    }
                }
            }
            $d.medios = $medios
            if ($listaExportar.Count -eq 0 -or $listaExportar -contains $i) {
                $png = Join-Path $carpeta ("diapo_{0:D2}.png" -f $i)
                $s.Export($png, "PNG", 1920, 1080)
                $d.png = $png
            }
            $diapos += $d
        }
        $informe.diapositivas_detalle = $diapos

        if ($GuardarCopia -ne "") {
            $pres.SaveCopyAs($GuardarCopia)
            $informe.copia_powerpoint = $GuardarCopia
        }
        # La prueba en ventana va al final: al terminarla, PowerPoint cierra la
        # presentación que se abrió sin ventana (medido).
        if ($ProbarShow) {
            try { $informe.show = ProbarShow $pres }
            catch { $informe.show_error = $_.Exception.Message }
        }
        $informe.resultado = "OK"
    }
    finally {
        # Al terminar la prueba en ventana, PowerPoint puede haber cerrado ya la
        # presentación (abierta sin ventana): Close() daría "Object does not exist".
        try { $pres.Close() } catch { $informe.nota_cierre = "la presentacion ya estaba cerrada al terminar" }
    }
    return $informe
}

function ProbarShow($pres) {
    $ss = $pres.SlideShowSettings
    $ss.ShowType = 2  # ppShowTypeWindow: en una ventana, no a pantalla completa
    $tRun = Get-Date
    $win = $ss.Run()
    $medidas = @([ordered]@{ run_devolvio_en_ms = [int]((Get-Date) - $tRun).TotalMilliseconds })
    try {
        $win.Left = 0; $win.Top = 0; $win.Width = 320; $win.Height = 180
        $view = $win.View
        $hasta = $pres.Slides.Count
        if ($ProbarHasta -gt 0 -and $ProbarHasta -lt $hasta) { $hasta = $ProbarHasta }
        for ($i = 1; $i -le $hasta; $i++) {
            if ($i -gt 1) { $view.Next() }  # como el clicker: siguiente
            $t = Get-Date
            $id = $null
            foreach ($sh in $view.Slide.Shapes) { if ($sh.Type -eq 16) { $id = $sh.Id } }
            $jugador = $view.Player($id)
            $muestras = @()
            foreach ($ms in @(300, 1200, 2000, 4200)) {
                $falta = $ms - ((Get-Date) - $t).TotalMilliseconds
                if ($falta -gt 0) { Start-Sleep -Milliseconds ([int]$falta) }
                # estado: 0 reproduciendo, 1 en pausa, 2 detenido (PpPlayerState)
                $muestras += ("{0} ms ({1} ms desde Run): posicion {2}, estado {3}" -f $ms, [int]((Get-Date) - $tRun).TotalMilliseconds, $jugador.CurrentPosition, $jugador.State)
            }
            $medidas += [ordered]@{ diapositiva = $view.Slide.SlideIndex; reproductor = $muestras }
        }
    }
    finally { try { $win.View.Exit() } catch { } }
    return $medidas
}

$app = New-Object -ComObject PowerPoint.Application
$alertas = $app.DisplayAlerts
$app.DisplayAlerts = 1  # ppAlertsNone
try {
    $informe = Revisar $app
}
catch {
    $informe = [ordered]@{ archivo = $ruta; resultado = "FALLA"; error = $_.Exception.Message }
}
finally {
    $app.DisplayAlerts = $alertas
    if (-not $NoCerrarApp) { $app.Quit() }
    [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($app)
    $app = $null
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
$informe | ConvertTo-Json -Depth 6 | Out-File -FilePath $archivoInforme -Encoding utf8
