import { useEffect, useRef, useState } from "react";
import type { FeatureCollection, GeoJsonProperties, Geometry } from "geojson";
import { Home, MapPin } from "lucide-react";
import maplibregl from "maplibre-gl";
import { useTranslation } from "react-i18next";

const BOROUGH_SOURCE_ID = "london-boroughs";
const BOROUGH_FILL_ID = "london-boroughs-fill";
const BOROUGH_GLOW_ID = "london-boroughs-glow";
const BOROUGH_LINE_ID = "london-boroughs-line";
const BOROUGH_SELECTED_LINE_ID = "london-boroughs-selected-line";
const DEFAULT_CAMERA = {
    center: [-0.118092, 51.509865] as [number, number],
    zoom: 9.2,
    bearing: 0,
    pitch: 0,
};

type MapStageProps = {
    hoveredBorough: string | null;
    selectedBorough: string | null;
    onHoverBorough: (boroughName: string | null) => void;
    onSelectBorough: (boroughName: string) => void;
};

type TooltipState = {
    name: string;
    x: number;
    y: number;
};

export function MapStage({ hoveredBorough, selectedBorough, onHoverBorough, onSelectBorough }: MapStageProps) {
    const { t, i18n } = useTranslation();
    const mapContainerRef = useRef<HTMLDivElement | null>(null);
    const mapRef = useRef<maplibregl.Map | null>(null);
    const geojsonRef = useRef<FeatureCollection<Geometry, GeoJsonProperties> | null>(null);
    const focusedBoroughRef = useRef<string | null>(null);
    const [mapStatus, setMapStatus] = useState<"loading" | "missing" | "fallback" | "loaded">("loading");
    const [mapReady, setMapReady] = useState(false);
    const [tooltip, setTooltip] = useState<TooltipState | null>(null);

    useEffect(() => {
        if (!mapContainerRef.current || mapRef.current) {
            return;
        }

        const map = new maplibregl.Map({
            container: mapContainerRef.current,
            ...DEFAULT_CAMERA,
            attributionControl: false,
            style: {
                version: 8,
                sources: {},
                layers: [
                    {
                        id: "map-background",
                        type: "background",
                        paint: {
                            "background-color": "#F1F5F9",
                        },
                    },
                ],
            },
        });

        mapRef.current = map;
        map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-left");
        localizeMapControls(mapContainerRef.current, t);

        map.on("load", async () => {
            try {
                const response = await fetch("/data/london_boroughs.geojson");

                if (!response.ok) {
                    setMapStatus("missing");
                    return;
                }

                const geojson = (await response.json()) as FeatureCollection<Geometry, GeoJsonProperties>;
                geojsonRef.current = geojson;

                if (!map.getSource(BOROUGH_SOURCE_ID)) {
                    map.addSource(BOROUGH_SOURCE_ID, {
                        type: "geojson",
                        data: geojson,
                    });

                    map.addLayer({
                        id: BOROUGH_FILL_ID,
                        type: "fill",
                        source: BOROUGH_SOURCE_ID,
                        paint: {
                            "fill-color": "#DBEAFE",
                            "fill-opacity": 0.5,
                        },
                    });

                    map.addLayer({
                        id: BOROUGH_GLOW_ID,
                        type: "line",
                        source: BOROUGH_SOURCE_ID,
                        paint: {
                            "line-color": "#60A5FA",
                            "line-width": 0,
                            "line-blur": 8,
                            "line-opacity": 0,
                        },
                    });
                    map.setPaintProperty(BOROUGH_GLOW_ID, "line-width-transition", {
                        duration: 250,
                        delay: 0,
                    });
                    map.setPaintProperty(BOROUGH_GLOW_ID, "line-opacity-transition", {
                        duration: 250,
                        delay: 0,
                    });

                    map.addLayer({
                        id: BOROUGH_LINE_ID,
                        type: "line",
                        source: BOROUGH_SOURCE_ID,
                        paint: {
                            "line-color": "#60A5FA",
                            "line-width": 1.2,
                            "line-opacity": 0.78,
                        },
                    });

                    map.addLayer({
                        id: BOROUGH_SELECTED_LINE_ID,
                        type: "line",
                        source: BOROUGH_SOURCE_ID,
                        paint: {
                            "line-color": "#2563EB",
                            "line-width": 0,
                            "line-opacity": 0,
                        },
                    });

                    map.on("mousemove", BOROUGH_FILL_ID, (event) => {
                        map.getCanvas().style.cursor = "pointer";
                        const boroughName = getBoroughName(event.features?.[0]?.properties);

                        if (!boroughName) {
                            return;
                        }

                        onHoverBorough(boroughName);
                        setTooltip({
                            name: boroughName,
                            x: event.point.x,
                            y: event.point.y,
                        });
                    });

                    map.on("mouseleave", BOROUGH_FILL_ID, () => {
                        map.getCanvas().style.cursor = "";
                        onHoverBorough(null);
                        setTooltip(null);
                    });

                    map.on("click", BOROUGH_FILL_ID, (event) => {
                        const boroughName = getBoroughName(event.features?.[0]?.properties);

                        if (!boroughName) {
                            return;
                        }

                        onSelectBorough(boroughName);
                        setTooltip(null);
                    });
                }

                setMapStatus("loaded");
                setMapReady(true);
            } catch {
                setMapStatus("fallback");
            }
        });

        return () => {
            map.remove();
            mapRef.current = null;
        };
    }, [onHoverBorough, onSelectBorough]);

    useEffect(() => {
        localizeMapControls(mapContainerRef.current, t);
    }, [i18n.resolvedLanguage, t]);

    useEffect(() => {
        const map = mapRef.current;

        if (!map || !mapReady || !map.getLayer(BOROUGH_FILL_ID)) {
            return;
        }

        map.setPaintProperty(BOROUGH_FILL_ID, "fill-color", [
            "case",
            ["==", ["get", "name"], selectedBorough ?? ""],
            "#3B82F6",
            ["==", ["get", "name"], hoveredBorough ?? ""],
            "#60A5FA",
            "#DBEAFE",
        ]);

        map.setPaintProperty(BOROUGH_FILL_ID, "fill-opacity", [
            "case",
            ["==", ["get", "name"], selectedBorough ?? ""],
            0.72,
            ["==", ["get", "name"], hoveredBorough ?? ""],
            0.68,
            ["!=", selectedBorough ?? "", ""],
            0.22,
            0.5,
        ]);

        map.setPaintProperty(BOROUGH_LINE_ID, "line-opacity", [
            "case",
            ["==", ["get", "name"], selectedBorough ?? ""],
            0.92,
            ["==", ["get", "name"], hoveredBorough ?? ""],
            0.9,
            ["!=", selectedBorough ?? "", ""],
            0.34,
            0.78,
        ]);

        map.setPaintProperty(BOROUGH_GLOW_ID, "line-width", [
            "case",
            ["==", ["get", "name"], hoveredBorough ?? ""],
            7,
            ["==", ["get", "name"], selectedBorough ?? ""],
            9,
            0,
        ]);

        map.setPaintProperty(BOROUGH_GLOW_ID, "line-opacity", [
            "case",
            ["any", ["==", ["get", "name"], hoveredBorough ?? ""], ["==", ["get", "name"], selectedBorough ?? ""]],
            0.9,
            0,
        ]);

        map.setPaintProperty(BOROUGH_SELECTED_LINE_ID, "line-width", [
            "case",
            ["==", ["get", "name"], selectedBorough ?? ""],
            3,
            0,
        ]);

        map.setPaintProperty(BOROUGH_SELECTED_LINE_ID, "line-opacity", [
            "case",
            ["==", ["get", "name"], selectedBorough ?? ""],
            1,
            0,
        ]);

        if (selectedBorough && focusedBoroughRef.current !== selectedBorough) {
            fitMapToBorough(map, geojsonRef.current, selectedBorough);
            focusedBoroughRef.current = selectedBorough;
        }
    }, [hoveredBorough, mapReady, selectedBorough]);

    const resetView = () => {
        mapRef.current?.easeTo({
            ...DEFAULT_CAMERA,
            duration: 300,
        });
    };

    return (
        <section className="relative overflow-hidden rounded-lg bg-surface shadow-panel">
            <div ref={mapContainerRef} className="h-full min-h-[640px] w-full" />
            <button
                type="button"
                className="absolute left-[10px] top-[80px] z-10 flex h-[30px] w-[30px] items-center justify-center rounded-[4px] bg-white text-text-primary shadow-[0_1px_4px_rgba(0,0,0,0.18)] transition-colors duration-fast hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                onClick={resetView}
                aria-label={t("map.reset")}
                title={t("map.reset")}
            >
                <Home size={16} aria-hidden="true" />
            </button>

            <div
                className={`pointer-events-none absolute left-[52px] top-md max-w-[calc(100%-68px)] rounded-md bg-white/80 px-md py-sm shadow-card backdrop-blur transition-opacity duration-slow ${selectedBorough ? "opacity-55" : "opacity-100"}`}
            >
                <div className="flex items-center gap-xs">
                    <MapPin size={17} className="text-primary" aria-hidden="true" />
                    <h2 className="text-caption font-semibold text-text-primary">{t("map.london")}</h2>
                </div>
                <p className="mt-xs text-caption text-text-secondary">
                    {t("map.hint")}
                </p>
                {mapStatus !== "loaded" ? (
                    <p className="mt-xs text-caption text-text-secondary">{t(`map.${mapStatus}`)}</p>
                ) : null}
            </div>

            {tooltip ? (
                <div
                    className="pointer-events-none absolute z-10 rounded-sm bg-white px-md py-sm text-caption font-semibold text-text-primary shadow-panel"
                    style={{
                        left: tooltip.x + 14,
                        top: tooltip.y + 14,
                    }}
                >
                    {tooltip.name}
                </div>
            ) : null}
        </section>
    );
}

function setControlLabel(control: HTMLButtonElement | null | undefined, label: string) {
    if (!control) return;
    control.setAttribute("aria-label", label);
    control.title = label;
}

function localizeMapControls(container: HTMLDivElement | null, t: (key: string) => string) {
    setControlLabel(container?.querySelector<HTMLButtonElement>(".maplibregl-ctrl-zoom-in"), t("map.zoomIn"));
    setControlLabel(container?.querySelector<HTMLButtonElement>(".maplibregl-ctrl-zoom-out"), t("map.zoomOut"));
}

function getBoroughName(properties: unknown): string | null {
    if (!properties || typeof properties !== "object") {
        return null;
    }

    const name = (properties as { name?: unknown }).name;
    return typeof name === "string" ? name : null;
}

function fitMapToBorough(
    map: maplibregl.Map,
    geojson: FeatureCollection<Geometry, GeoJsonProperties> | null,
    boroughName: string,
) {
    const feature = geojson?.features.find((candidate) => candidate.properties?.name === boroughName);

    if (!feature?.geometry) {
        return;
    }

    const bounds = getGeometryBounds(feature.geometry);

    if (!bounds) {
        return;
    }

    map.fitBounds(bounds, {
        padding: 96,
        duration: 300,
        maxZoom: 11.4,
    });
}

function getGeometryBounds(geometry: Geometry): maplibregl.LngLatBounds | null {
    const bounds = new maplibregl.LngLatBounds();
    let hasCoordinate = false;

    const visitCoordinates = (value: unknown) => {
        if (!Array.isArray(value)) {
            return;
        }

        if (value.length >= 2 && typeof value[0] === "number" && typeof value[1] === "number") {
            bounds.extend([value[0], value[1]]);
            hasCoordinate = true;
            return;
        }

        value.forEach(visitCoordinates);
    };

    const visitGeometry = (value: Geometry) => {
        if (value.type === "GeometryCollection") {
            value.geometries.forEach(visitGeometry);
            return;
        }

        visitCoordinates(value.coordinates);
    };

    visitGeometry(geometry);
    return hasCoordinate ? bounds : null;
}
