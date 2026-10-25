import { useFonts } from "expo-font";
import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { colors, globalStyles } from "./styles/global";

const rows = require("../assets/predictions.json");

const SPOTS = ["spot_1", "spot_2", "spot_3", "spot_4", "spot_5"];
const DAYS = ["su", "mo", "tu", "we", "th", "fr", "sa"];
const BUCKETS = ["12-6a", "6a-12p", "12-6p", "6p-12a"];
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

const BUSY = 0.5;
const font = "Montserrat-Bold";

// hermes wont parse this with new Date
function toDate(ts: string) {
  const [day, time] = ts.split(" ");
  const [y, mo, d] = day.split("-");
  const [h, mi] = time.split(":");
  return new Date(+y, +mo - 1, +d, +h, +mi);
}

const dates = rows.map((r: any) => toDate(r.timestamp));
const first = dates[0];
const last = dates[dates.length - 1];

function fmt(d: Date) {
  return MONTHS[d.getMonth()] + " " + d.getDate();
}

function bucket(h: number) {
  if (h < 6) return 0;
  if (h < 12) return 1;
  if (h < 18) return 2;
  return 3;
}

function nearest(t: number) {
  let best = 0;
  let gap = Math.abs(dates[0].getTime() - t);

  for (let i = 1; i < dates.length; i++) {
    const g = Math.abs(dates[i].getTime() - t);

    if (g < gap) {
      gap = g;
      best = i;
    }
  }

  return best;
}

function gridFor(spot: string) {
  const sums = DAYS.map(() => [0, 0, 0, 0]);
  const counts = DAYS.map(() => [0, 0, 0, 0]);

  for (let i = 0; i < rows.length; i++) {
    const d = dates[i];
    const b = bucket(d.getHours());
    const r = rows[i];

    let v = 0;

    if (spot === "all") {
      for (const k of SPOTS) {
        v += r[k];
      }

      v = v / SPOTS.length;
    } else {
      v = r[spot];
    }

    sums[d.getDay()][b] += v;
    counts[d.getDay()][b] += 1;
  }

  return sums.map((day, di) =>
    day.map((sum, bi) => {
      if (counts[di][bi] === 0) {
        return null;
      }

      return sum / counts[di][bi];
    }),
  );
}

function shade(v: number | null) {
  if (v === null) return "#f4f4f6";
  if (v < 0.15) return "#e9eaf1";
  if (v < 0.4) return "#b6b9d1";
  if (v < 0.65) return "#6b7099";

  return colors.header;
}

let flat = rows.length > 1;

for (let i = 1; i < rows.length; i++) {
  if (SPOTS.some((k) => rows[i][k] !== rows[0][k])) {
    flat = false;
    break;
  }
}

export default function Predictions() {
  const [spot, setSpot] = useState("all");
  const [now, setNow] = useState(new Date());

  const [fontsLoaded] = useFonts({
    "Montserrat-Bold": require("../assets/fonts/Montserrat-VariableFont_wght.ttf"),
  });

  useEffect(() => {
    const id = setInterval(() => {
      setNow(new Date());
    }, 60000);

    return () => clearInterval(id);
  }, []);

  if (!fontsLoaded) return null;

  if (rows.length === 0) {
    return (
      <View style={globalStyles.container}>
        <Text style={{ fontFamily: font, fontSize: 30, color: colors.header }}>
          Forecast
        </Text>

        <Text style={{ ...globalStyles.empty, marginTop: 8 }}>no data</Text>
      </View>
    );
  }

  const t = now.getTime();
  const row = rows[nearest(t)];
  const at = toDate(row.timestamp);

  const inWeek = t >= first.getTime() && t <= last.getTime();
  const open = SPOTS.filter((k) => row[k] <= BUSY).length;

  const grid = gridFor(spot);
  const nowDay = now.getDay();
  const nowBucket = bucket(now.getHours());

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 20, paddingTop: 60, paddingBottom: 40 }}
    >
      <Text
        style={{ fontFamily: font, fontSize: 14, color: colors.textSecondary }}
      >
        Forecast
      </Text>

      <Text
        style={{
          fontFamily: font,
          fontSize: 44,
          color: colors.header,
          marginTop: 2,
        }}
      >
        {open} / 5 open
      </Text>

      <Text style={{ fontSize: 13, color: colors.textSecondary, marginTop: 3 }}>
        {fmt(first)} to {fmt(last)}, {rows.length} points
      </Text>

      {flat && (
        <View style={s.banner}>
          <Text style={{ color: colors.alert, fontSize: 13 }}>
            same numbers every row, regen predictions.json
          </Text>
        </View>
      )}

      {!inWeek && (
        <Text
          style={{ fontSize: 13, color: colors.textSecondary, marginTop: 8 }}
        >
          outside the forecast week, showing {fmt(at)}
        </Text>
      )}

      <Text
        style={{
          fontFamily: font,
          fontSize: 16,
          color: colors.text,
          marginTop: 22,
          marginBottom: 10,
        }}
      >
        {fmt(at)}, per spot
      </Text>

      {SPOTS.map((k, n) => {
        const p = row[k];

        return (
          <View key={k} style={s.bar}>
            <Text
              style={{ width: 18, fontSize: 13, color: colors.textSecondary }}
            >
              {n + 1}
            </Text>

            <View style={s.track}>
              <View style={[s.fill, { width: `${Math.max(p * 100, 2)}%` }]} />
            </View>

            <Text
              style={{
                width: 38,
                textAlign: "right",
                fontSize: 13,
                color: colors.text,
              }}
            >
              {Math.round(p * 100)}%
            </Text>

            <Text
              style={{
                width: 40,
                textAlign: "right",
                fontSize: 12,
                color: p > BUSY ? colors.alert : colors.textSecondary,
              }}
            >
              {p > BUSY ? "busy" : "open"}
            </Text>
          </View>
        );
      })}

      <Text
        style={{
          fontFamily: font,
          fontSize: 16,
          color: colors.text,
          marginTop: 34,
          marginBottom: 10,
        }}
      >
        this week
      </Text>

      <View
        style={{
          flexDirection: "row",
          flexWrap: "wrap",
          gap: 6,
          marginBottom: 14,
        }}
      >
        {["all", ...SPOTS].map((k) => {
          const on = spot === k;

          return (
            <Pressable
              key={k}
              onPress={() => setSpot(k)}
              style={[s.chip, on && { backgroundColor: colors.header }]}
            >
              <Text
                style={{ fontSize: 12, color: on ? "#ffffff" : colors.text }}
              >
                {k === "all" ? "all" : k.slice(-1)}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <View style={{ flexDirection: "row", marginBottom: 4 }}>
        <View style={{ width: 22 }} />

        {BUCKETS.map((b) => (
          <Text
            key={b}
            style={{
              flex: 1,
              marginHorizontal: 2,
              textAlign: "center",
              fontSize: 10,
              color: colors.textSecondary,
            }}
          >
            {b}
          </Text>
        ))}
      </View>

      {grid.map((cells, di) => (
        <View
          key={DAYS[di]}
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginBottom: 3,
          }}
        >
          <Text
            style={{ width: 22, fontSize: 11, color: colors.textSecondary }}
          >
            {DAYS[di]}
          </Text>

          {cells.map((v, bi) => (
            <View
              key={bi}
              style={[
                s.cell,
                { backgroundColor: shade(v) },
                inWeek &&
                  di === nowDay &&
                  bi === nowBucket && {
                    borderWidth: 2,
                    borderColor: colors.alert,
                  },
              ]}
            >
              <Text
                style={{
                  fontSize: 10,
                  color: v !== null && v >= 0.4 ? "#ffffff" : colors.text,
                }}
              >
                {v === null ? "" : Math.round(v * 100) + "%"}
              </Text>
            </View>
          ))}
        </View>
      ))}

      <Text style={{ ...globalStyles.empty, fontSize: 12, marginTop: 10 }}>
        avg over 6 hrs
      </Text>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  bar: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
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

  cell: {
    flex: 1,
    height: 26,
    marginHorizontal: 2,
    borderRadius: 2,
    alignItems: "center",
    justifyContent: "center",
  },

  banner: {
    borderLeftWidth: 2,
    borderLeftColor: colors.alert,
    paddingLeft: 9,
    marginTop: 16,
  },
});
