
import AppKit
import Foundation
let args = CommandLine.arguments
print("SVG_registered=" + String(NSImage.imageTypes.contains("public.svg-image")))
guard args.count == 3 else { fputs("Expected SVG input and PNG output\n", stderr); exit(2) }
guard let image = NSImage(contentsOfFile: args[1]) else {
    fputs("NSImage could not create a supported representation from this SVG document\n", stderr)
    exit(3)
}
var bounds = NSRect(origin: .zero, size: image.size)
guard let cgImage = image.cgImage(forProposedRect: &bounds, context: nil, hints: nil) else {
    fputs("NSImage representation did not produce a CGImage snapshot\n", stderr)
    exit(4)
}
let bitmap = NSBitmapImageRep(cgImage: cgImage)
guard let png = bitmap.representation(using: .png, properties: [:]) else { exit(5) }
do {
    try png.write(to: URL(fileURLWithPath: args[2]))
    print("PNG_dimensions=" + String(cgImage.width) + "x" + String(cgImage.height))
} catch { fputs("PNG write failed: \(error)\n", stderr); exit(6) }
