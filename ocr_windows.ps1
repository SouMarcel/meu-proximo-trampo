# OCR de PDF so de imagem com o que o Windows 10/11 ja traz (spec 037; chamado por ocr.py).
# Cada pagina vira imagem (Windows.Data.Pdf) e passa pelo OCR do sistema (Windows.Media.Ocr), sem rede.
# Saida: uma linha JSON em UTF-8 - {"paginas": N, "lidas": N, "textos": [...], "idioma": "pt-BR"} ou {"erro": "..."}.
# O arquivo fica so com ASCII: o PowerShell 5.1 le .ps1 sem BOM como ANSI.
param([Parameter(Mandatory = $true)][string]$Caminho, [int]$MaxPaginas = 5)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Responder($dados) { [Console]::Out.WriteLine(($dados | ConvertTo-Json -Compress -Depth 4)) }

try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    $null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
    $null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
    $null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
    $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
    $null = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]
    $null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]

    # as operacoes do WinRT sao assincronas: AsTask + Wait
    $metodos = [System.WindowsRuntimeSystemExtensions].GetMethods()
    $asTaskOp = ($metodos | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
            $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
    $asTaskAcao = ($metodos | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
            $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' })[0]
    function Esperar($op, [Type]$tipo) { $t = $asTaskOp.MakeGenericMethod($tipo).Invoke($null, @($op)); $null = $t.Wait(-1); $t.Result }
    function EsperarAcao($op) { $t = $asTaskAcao.Invoke($null, @($op)); $null = $t.Wait(-1) }

    $motor = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new("pt-BR"))
    if (-not $motor) { $motor = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages() }
    if (-not $motor) { Responder @{ erro = "sem OCR neste Windows (falta um idioma com reconhecimento de texto)" }; exit 0 }

    $arquivo = Esperar ([Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path -LiteralPath $Caminho).Path)) ([Windows.Storage.StorageFile])
    $pdf = Esperar ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($arquivo)) ([Windows.Data.Pdf.PdfDocument])

    # le uma pagina com o lado maior em $lado pixels (o OCR do Windows erra em imagem grande demais)
    function LerPagina($pagina, [double]$lado) {
        $fluxo = [Windows.Storage.Streams.InMemoryRandomAccessStream]::new()
        $opcoes = [Windows.Data.Pdf.PdfPageRenderOptions]::new()
        $escala = [Math]::Min(4.0, $lado / [Math]::Max($pagina.Size.Width, $pagina.Size.Height))
        $opcoes.DestinationWidth = [uint32]([Math]::Max(1, $pagina.Size.Width * $escala))
        $opcoes.DestinationHeight = [uint32]([Math]::Max(1, $pagina.Size.Height * $escala))
        EsperarAcao ($pagina.RenderToStreamAsync($fluxo, $opcoes))
        $decodificador = Esperar ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($fluxo)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $imagem = Esperar ($decodificador.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $resultado = Esperar ($motor.RecognizeAsync($imagem)) ([Windows.Media.Ocr.OcrResult])
        (@($resultado.Lines | ForEach-Object { $_.Text }) -join "`n")
    }
    function Letras([string]$texto) { ([regex]::Matches($texto, '\p{L}')).Count }

    $lidas = [Math]::Min([int]$pdf.PageCount, [Math]::Max(1, $MaxPaginas))
    $textos = New-Object System.Collections.Generic.List[string]
    for ($i = 0; $i -lt $lidas; $i++) {
        $pagina = $pdf.GetPage([uint32]$i)
        $melhor = LerPagina $pagina 1600
        if ((Letras $melhor) -lt 40) {
            foreach ($lado in 1200, 2400) {
                $outro = LerPagina $pagina $lado
                if ((Letras $outro) -gt (Letras $melhor)) { $melhor = $outro }
            }
        }
        $textos.Add([string]$melhor)
        $pagina.Dispose()
    }
    Responder @{ paginas = [int]$pdf.PageCount; lidas = $lidas; textos = $textos.ToArray(); idioma = $motor.RecognizerLanguage.LanguageTag }
}
catch {
    Responder @{ erro = ($_.Exception.Message -replace '\s+', ' ').Trim() }
}
