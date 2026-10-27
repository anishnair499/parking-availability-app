# LotLink app

The Expo (React Native) app for LotLink. See the [main README](../README.md) for what the project does and how the pieces fit together.

## Run it

```bash
npm install
npx expo start
```

Press `w` for the web version, or scan the QR code with the Expo Go app.

## Where things are

- `app/`: one file per tab. `index.tsx` (Home), `parking.tsx` (live map), `model.tsx`, `predictions.tsx` (Forecast), `settings.tsx`. `_layout.tsx` sets up the tab bar.
- `components/ParkingLotLayout.tsx`: the SVG map of the lot, colored by live sensor readings
- `components/styles/global.ts`: shared colors and text styles
- `lib/firebase.ts`: the one shared Firebase app every screen uses
