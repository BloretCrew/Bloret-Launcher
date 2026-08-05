import QtQuick 2.15
import RinUI

/**
 * Dotted thinking-orb indicator (inspired by https://orbs.jakubantalik.com).
 * Pure QML Canvas — monochrome dots on tilted orbital rings.
 */
Item {
    id: root

    property int size: 20
    property bool running: true
    property real speed: 1.0
    // working | composing | searching | breathing
    property string state: "composing"
    property color ink: Theme.currentTheme.colors.textColor
    property real inkOpacity: 0.85

    width: size
    height: size
    implicitWidth: size
    implicitHeight: size

    property real _t: 0

    NumberAnimation on _t {
        id: clock
        from: 0
        to: Math.PI * 200
        duration: Math.max(8000, 24000 / Math.max(0.25, root.speed))
        loops: Animation.Infinite
        running: root.running && root.visible
    }

    onRunningChanged: if (running) canvas.requestPaint()
    onStateChanged: canvas.requestPaint()
    onInkChanged: canvas.requestPaint()
    on_tChanged: if (running) canvas.requestPaint()
    onSizeChanged: canvas.requestPaint()

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true
        renderTarget: Canvas.Image
        renderStrategy: Canvas.Cooperative

        onPaint: {
            var ctx = getContext("2d")
            var w = width
            var h = height
            ctx.clearRect(0, 0, w, h)

            var cx = w / 2
            var cy = h / 2
            var R = Math.min(w, h) * 0.42
            var t = root._t
            var ink = root.ink
            var baseA = root.inkOpacity

            function setInk(a) {
                // Qt Canvas accepts css rgba
                var c = ink
                // Theme colors may be QColor-like strings "#RRGGBB" or "rgba..."
                ctx.fillStyle = ink
                ctx.globalAlpha = Math.max(0, Math.min(1, a))
            }

            function dot(x, y, r, a) {
                setInk(a)
                ctx.beginPath()
                ctx.arc(x, y, r, 0, Math.PI * 2)
                ctx.fill()
            }

            // Project a 3D point on a tilted ring into 2D with simple perspective
            function project(angle, ringR, tilt, phase, yOff) {
                var a = angle + phase
                var x3 = Math.cos(a) * ringR
                var y3 = Math.sin(a) * ringR * Math.sin(tilt) + (yOff || 0)
                var z3 = Math.sin(a) * ringR * Math.cos(tilt)
                var persp = 1 / (1.55 - z3 / (R * 1.2))
                return {
                    x: cx + x3 * persp,
                    y: cy + y3 * persp,
                    z: z3,
                    s: persp
                }
            }

            var st = root.state
            var rings = 3
            var dotsPerRing = root.size >= 40 ? 18 : (root.size >= 28 ? 14 : 10)
            var dotR = Math.max(0.8, root.size * 0.045)

            if (st === "breathing") {
                var breathe = 0.85 + 0.15 * Math.sin(t * 1.2)
                for (var i = 0; i < dotsPerRing; i++) {
                    var ang = (i / dotsPerRing) * Math.PI * 2
                    var p = project(ang, R * breathe, 0.55, t * 0.35, 0)
                    var depth = (p.z / R + 1) * 0.5
                    dot(p.x, p.y, dotR * (0.7 + 0.6 * p.s), baseA * (0.35 + 0.65 * depth))
                }
            } else if (st === "searching") {
                // Globe + sweeping meridian highlight
                for (var ri = 0; ri < rings; ri++) {
                    var rr = R * (0.45 + ri * 0.25)
                    var tilt = 0.35 + ri * 0.25
                    for (var j = 0; j < dotsPerRing; j++) {
                        var ang2 = (j / dotsPerRing) * Math.PI * 2
                        var p2 = project(ang2, rr, tilt, t * 0.2, 0)
                        var meridian = Math.abs(Math.sin(ang2 - t * 1.4))
                        var hi = Math.pow(1 - meridian, 6)
                        var depth2 = (p2.z / R + 1) * 0.5
                        dot(p2.x, p2.y, dotR * (0.6 + 0.7 * p2.s + hi * 0.5),
                            baseA * (0.25 + 0.55 * depth2 + hi * 0.45))
                    }
                }
            } else if (st === "working") {
                // Particles racing on tilted orbits
                for (var r2 = 0; r2 < rings; r2++) {
                    var rr2 = R * (0.4 + r2 * 0.28)
                    var tilt2 = 0.5 + r2 * 0.2
                    var spin = t * (0.6 + r2 * 0.35) * (r2 % 2 === 0 ? 1 : -1)
                    var n = dotsPerRing - r2 * 2
                    for (var k = 0; k < n; k++) {
                        var ang3 = (k / n) * Math.PI * 2
                        var p3 = project(ang3, rr2, tilt2, spin, 0)
                        var depth3 = (p3.z / R + 1) * 0.5
                        // lead particles brighter
                        var lead = Math.pow((Math.sin(ang3 * 2 + spin * 3) + 1) * 0.5, 3)
                        dot(p3.x, p3.y, dotR * (0.65 + 0.7 * p3.s + lead * 0.4),
                            baseA * (0.3 + 0.5 * depth3 + lead * 0.35))
                    }
                }
            } else {
                // composing (default): undulating multi-band sash
                for (var r3 = 0; r3 < rings; r3++) {
                    var rr3 = R * (0.42 + r3 * 0.26)
                    var tilt3 = 0.4 + r3 * 0.28
                    var phase = t * (0.45 + r3 * 0.15) + r3 * 0.9
                    var n3 = dotsPerRing
                    for (var m = 0; m < n3; m++) {
                        var ang4 = (m / n3) * Math.PI * 2
                        var wave = Math.sin(ang4 * 3 + t * 1.8 + r3) * R * 0.08
                        var p4 = project(ang4, rr3, tilt3, phase, wave)
                        var depth4 = (p4.z / R + 1) * 0.5
                        var sash = 0.5 + 0.5 * Math.sin(ang4 * 2 - t * 1.2 + r3)
                        dot(p4.x, p4.y, dotR * (0.6 + 0.75 * p4.s),
                            baseA * (0.28 + 0.5 * depth4 + 0.25 * sash))
                    }
                }
                // soft core
                setInk(baseA * 0.35)
                ctx.beginPath()
                ctx.arc(cx, cy, Math.max(1.2, root.size * 0.06), 0, Math.PI * 2)
                ctx.fill()
            }

            ctx.globalAlpha = 1
        }
    }

    // Static fallback when not running: single ring of dots
    Component.onCompleted: canvas.requestPaint()
}
