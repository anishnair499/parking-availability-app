import { useFonts } from "expo-font";
import { doc, onSnapshot } from "firebase/firestore";
import { useEffect, useState } from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from "react-native";
import Svg, { Line, Polyline, Rect } from "react-native-svg";
import { colors, globalStyles } from "../components/styles/global";
import { db } from "../lib/firebase";

const font = "Montserrat-Bold";
const MONTHS = [
  "jan",
  "feb",
  "mar",
  "apr",
  "may",
  "jun",
  "jul",
  "aug",
  "sep",
  "oct",
  "nov",
  "dec",
];

// sensors go live sep 6
const CAPTURE_START = new Date(2026, 8, 6);
const LSTM_DAYS = 21;

const STALE_MINS = 15;
const CH = 90;

// hermes wont parse this with new Date
function toDate(ts: string) {
  const [day, time] = ts.split(" ");
  const [y, mo, d] = day.split("-");
  const [h, mi] = time.split(":");
  return new Date(+y, +mo - 1, +d, +h, +mi);
}

function fmt(d: Date) {
  return MONTHS[d.getMonth()] + " " + d.getDate();
}

function pct(v: number) {
  return Math.round(v * 100) + "%";
}

function compact(n: number) {
  return n >= 1000 ? (n / 1000).toFixed(1) + "k" : String(n);
}

function minsSince(d: Date) {
  return Math.round((Date.now() - d.getTime()) / 60000);
}

export default function Model() {
  const [status, setStatus] = useState<any>(null);
  const [recent, setRecent] = useState<any>(null);
  const [err, setErr] = useState("");
  const [spot, setSpot] = useState(0);
  const { width } = useWindowDimensions();

  const [fontsLoaded] = useFonts({
    "Montserrat-Bold": require("../assets/fonts/Montserrat-VariableFont_wght.ttf"),
  });

  useEffect(() => {
    const unSubscribe = onSnapshot(
      doc(db, "models", "status"),
      (snapshot) => {
        if (snapshot.exists()) {
          setStatus(snapshot.data());
        } else {
          setStatus(null);
        }
      },
      (error) => setErr(error.message),
    );

    return () => unSubscribe();
  }, []);

  useEffect(() => {
    const unSubscribe = onSnapshot(
      doc(db, "models", "recent"),
      (snapshot) => {
        if (snapshot.exists()) {
          setRecent(snapshot.data());
        } else {
          setRecent(null);
        }
      },
      (error) => setErr(error.message),
    );

    return () => unSubscribe();
  }, []);

  if (!fontsLoaded) return null;

  if (err) {
    return (
      <View style={globalStyles.container}>
        <Text style={{ fontFamily: font, fontSize: 30, color: colors.header }}>
          Model
        </Text>

        <View style={s.banner}>
          <Text style={{ color: colors.alert, fontSize: 13 }}>
            cant reach firestore: {err}
          </Text>
        </View>

        <Text style={{ ...globalStyles.empty, marginTop: 10 }}>
          check the apiKey and projectId in lib/firebase.ts
        </Text>
      </View>
    );
  }

  if (!status) {
    const days = Math.floor((Date.now() - CAPTURE_START.getTime()) / 86400000);

    return (
      <ScrollView
        style={{ flex: 1, backgroundColor: colors.background }}
        contentContainerStyle={{
          padding: 20,
          paddingTop: 60,
          paddingBottom: 40,
        }}
      >
        <Text
          style={{
            fontFamily: font,
            fontSize: 14,
            color: colors.textSecondary,
          }}
        >
          Model
        </Text>

        <Text
          style={{
            fontFamily: font,
            fontSize: 44,
            color: colors.header,
            marginTop: 2,
          }}
        >
          collecting data
        </Text>

        {days < 0 ? (
          <Text
            style={{ fontSize: 13, color: colors.textSecondary, marginTop: 3 }}
          >
            sensors go live {fmt(CAPTURE_START)}
          </Text>
        ) : (
          <Text
            style={{ fontSize: 13, color: colors.textSecondary, marginTop: 3 }}
          >
            day {days} since {fmt(CAPTURE_START)}
          </Text>
        )}

        <Text style={s.h2}>whats waiting on what</Text>

        <Unlock label="lstm forecast" need={LSTM_DAYS} have={days} />
        <Text style={{ ...globalStyles.empty, fontSize: 12, marginTop: 12 }}>
          nothing to predict from yet. the lstm needs about three weeks of
          readings before it can learn the daily pattern.
        </Text>
      </ScrollView>
    );
  }

  const live = status.lstm ?? {};
  const info = status.data ?? {};

  const last = info.lastReading ? toDate(info.lastReading) : null;
  const stale = last ? minsSince(last) > STALE_MINS : false;

  const spots: string[] = recent?.spots ?? ["spot_1", "spot_2"];
  const pts: any[] = recent?.points ?? [];
  const si = Math.min(spot, spots.length - 1);

  const cw = Math.max(width - 40, 1);

  const xFor = (i: number) => {
    return (i / Math.max(pts.length - 1, 1)) * cw;
  };

  const yFor = (p: number) => {
    return CH - p * CH;
  };

  const bands: { x: number; w: number }[] = [];
  let run = -1;

  pts.forEach((p: any, i: number) => {
    const occupied = p.act?.[si] === 1;

    if (occupied && run < 0) {
      run = i;
    }

    if (run >= 0 && (!occupied || i === pts.length - 1)) {
      bands.push({
        x: xFor(run),
        w: Math.max(xFor(i) - xFor(run), 1),
      });

      run = -1;
    }
  });

  const line = pts
    .map((p: any, i: number) => {
      return xFor(i) + "," + yFor(p.pred?.[si] ?? 0);
    })
    .join(" ");

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 20, paddingTop: 60, paddingBottom: 40 }}
    >
      <Text
        style={{ fontFamily: font, fontSize: 14, color: colors.textSecondary }}
      >
        Model
      </Text>

      <Text
        style={{
          fontFamily: font,
          fontSize: 44,
          color: colors.header,
          marginTop: 2,
        }}
      >
        {live.accuracy != null
          ? pct(live.accuracy) + " accurate"
          : "no score yet"}
      </Text>

      <Text style={{ fontSize: 13, color: colors.textSecondary, marginTop: 3 }}>
        lstm
        {status.trainedAt ? " · trained " + fmt(toDate(status.trainedAt)) : ""}
        {info.rows != null ? " · " + compact(info.rows) + " readings" : ""}
      </Text>

      {stale && last && (
        <View style={s.banner}>
          <Text style={{ color: colors.alert, fontSize: 13 }}>
            no reading for {minsSince(last)} min, sensors or the cron job may be
            down
          </Text>
        </View>
      )}

      <Text style={s.h2}>how well it does</Text>

      {live.accuracy != null && (
        <View style={s.bar}>
          <Text style={{ width: 60, fontSize: 13, color: colors.text }}>
            lstm
          </Text>

          <View style={s.track}>
            <View
              style={[
                s.fill,
                { width: `${Math.max(live.accuracy * 100, 2)}%` },
              ]}
            />
          </View>

          <Text
            style={{
              width: 42,
              textAlign: "right",
              fontSize: 13,
              color: colors.text,
            }}
          >
            {pct(live.accuracy)}
          </Text>
        </View>
      )}

      <Text style={{ ...globalStyles.empty, fontSize: 12, marginTop: 8 }}>
        scored on the newest 20% of the readings, which the model never trained
        on.
      </Text>

      {pts.length > 0 && (
        <>
          <Text style={s.h2}>predicted vs what happened</Text>

          <View
            style={{
              flexDirection: "row",
              flexWrap: "wrap",
              gap: 6,
              marginBottom: 10,
            }}
          >
            {spots.map((k, i) => {
              const on = si === i;

              return (
                <Pressable
                  key={k}
                  onPress={() => setSpot(i)}
                  style={[s.chip, on && { backgroundColor: colors.header }]}
                >
                  <Text
                    style={{
                      fontSize: 12,
                      color: on ? "#ffffff" : colors.text,
                    }}
                  >
                    spot {i + 1}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <Svg width={cw} height={CH}>
            {bands.map((b, i) => (
              <Rect
                key={i}
                x={b.x}
                y={0}
                width={b.w}
                height={CH}
                fill="#e9eaf1"
              />
            ))}

            <Line
              x1={0}
              y1={yFor(0.5)}
              x2={cw}
              y2={yFor(0.5)}
              stroke="#d8d9e3"
              strokeWidth={1}
            />

            <Polyline
              points={line}
              fill="none"
              stroke={colors.header}
              strokeWidth={2}
            />
          </Svg>

          <Text style={{ ...globalStyles.empty, fontSize: 12, marginTop: 6 }}>
            shaded = actually occupied, line = what we predicted. {pts.length}{" "}
            hours
          </Text>
        </>
      )}

      <Text style={s.h2}>data</Text>

      <Row
        label="readings"
        value={info.rows != null ? compact(info.rows) : "-"}
      />
      <Row
        label="days of coverage"
        value={info.days != null ? String(info.days) : "-"}
      />
      <Row label="gaps" value={info.gaps != null ? String(info.gaps) : "-"} />
      <Row
        label="last reading"
        value={last ? minsSince(last) + " min ago" : "-"}
      />
      <Row
        label="last forecast"
        value={
          status.lastForecastRun ? fmt(toDate(status.lastForecastRun)) : "-"
        }
      />

      <Text style={s.h2}>how it works</Text>

      <Text style={{ fontSize: 13, color: colors.text, lineHeight: 20 }}>
        an esp32 reads two hc-sr04 distance sensors once a minute and writes
        whether each spot is taken up to firestore. the model reads the last
        four hours of that plus the time of day and guesses the week ahead. it
        retrains weekly as more readings pile up.
      </Text>
    </ScrollView>
  );
}

function Unlock({
  label,
  need,
  have,
}: {
  label: string;
  need: number;
  have: number;
}) {
  const done = have >= need;
  const p = Math.max(Math.min(have / need, 1), 0);

  return (
    <View style={s.bar}>
      <Text style={{ width: 128, fontSize: 13, color: colors.text }}>
        {label}
      </Text>

      <View style={s.track}>
        <View style={[s.fill, { width: `${Math.max(p * 100, 2)}%` }]} />
      </View>

      <Text
        style={{
          width: 66,
          textAlign: "right",
          fontSize: 12,
          color: colors.textSecondary,
        }}
      >
        {done ? "ready" : need - have + "d left"}
      </Text>
    </View>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={s.row}>
      <Text style={{ fontSize: 13, color: colors.textSecondary }}>{label}</Text>

      <Text style={{ fontSize: 13, color: colors.text }}>{value}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  h2: {
    fontFamily: font,
    fontSize: 16,
    color: colors.text,
    marginTop: 26,
    marginBottom: 10,
  },

  bar: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
  },

  track: {
    flex: 1,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#ededf2",
    overflow: "hidden",
  },

  fill: {
    height: 10,
    borderRadius: 5,
    backgroundColor: colors.header,
  },

  chip: {
    paddingHorizontal: 11,
    paddingVertical: 5,
    borderRadius: 999,
    backgroundColor: "#eeeef3",
  },

  pill: {
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 999,
    backgroundColor: colors.header,
  },

  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 7,
    borderBottomWidth: 1,
    borderBottomColor: "#f0f0f4",
  },

  banner: {
    borderLeftWidth: 2,
    borderLeftColor: colors.alert,
    paddingLeft: 9,
    marginTop: 16,
  },
});
