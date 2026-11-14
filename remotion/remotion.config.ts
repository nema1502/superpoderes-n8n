// Configuración de la CLI de Remotion (`pnpm studio`, `pnpm still`, `pnpm render`).
// render.mjs no la lee: lleva sus propias opciones, las mismas MÁS la receta de
// frontera (QP constante y cuadro clave al final). Los videos que van al
// PowerPoint salen de render.mjs; la CLI queda para borradores.
import { Config } from "@remotion/cli/config";

Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
Config.setCrf(18);
// BT.709 convertido y etiquetado: así PowerPoint, ffmpeg y el póster PNG leen
// los mismos colores (sin etiqueta, cada programa elige su matriz).
Config.setColorSpace("bt709");
// Cuadros en PNG antes de codificar: el texto queda nítido (JPEG ensucia los
// bordes de las letras antes de que h264 los vuelva a comprimir).
Config.setVideoImageFormat("png");
// 16 GB de RAM: cuatro pestañas de Chrome a la vez, no las ocho por defecto.
Config.setConcurrency(4);
Config.setOverwriteOutput(true);
// Los logos y las piezas de diseño se sirven desde diseno/ (lo mismo que usa render.mjs).
Config.setPublicDir("../diseno");
