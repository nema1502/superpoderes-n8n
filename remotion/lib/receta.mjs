// La receta de frontera (docs/infra.md §7): h264 High, yuv420p, BT.709 convertido y
// etiquetado, cuadros en PNG, QP CONSTANTE 16 (no CRF) y un cuadro clave forzado en el
// ÚLTIMO cuadro. Así el último cuadro de un paso y el primero del siguiente (el mismo
// número de cuadro de la composición) salen idénticos al bit en los dos videos.
export const QP_FRONTERA = 16;

export const OPCIONES_VIDEO = {
  codec: "h264",
  crf: 18, // la receta lo cambia por -qp 16
  pixelFormat: "yuv420p",
  imageFormat: "png",
  x264Preset: "medium",
  colorSpace: "bt709",
  muted: true,
};

/** ffmpegOverride: -crf N → -qp 16 y -force_key_frames en el último cuadro. Anota lo que aplicó. */
export function recetaFrontera(cuadros, registro) {
  return ({ type, args }) => {
    const i = args.indexOf("-crf");
    if (i === -1) return args;
    const nuevos = [...args];
    nuevos.splice(i, 2, "-qp", String(QP_FRONTERA));
    const y = nuevos.lastIndexOf("-y");
    nuevos.splice(y === -1 ? nuevos.length - 1 : y, 0, "-force_key_frames", `expr:eq(n,${cuadros - 1})`);
    registro.push({ type, args: nuevos });
    return nuevos;
  };
}

/** Opciones de renderMedia para un tramo de cuadros [a, b] (inclusivo) con la receta. */
export function opcionesTramo(a, b, crfBorrador = null) {
  const registro = [];
  const opciones = crfBorrador === null ? { ...OPCIONES_VIDEO, frameRange: [a, b], ffmpegOverride: recetaFrontera(b - a + 1, registro) } : { ...OPCIONES_VIDEO, crf: crfBorrador, frameRange: [a, b] };
  return { opciones, registro };
}
