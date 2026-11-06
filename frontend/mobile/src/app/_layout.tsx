import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { WorkspaceProvider } from "@/lib/workspace/store";
import { colors } from "@/theme";

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <WorkspaceProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: colors.surfaceSunken },
          }}
        >
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="farm/[id]" />
          <Stack.Screen name="analysis/index" />
          <Stack.Screen name="analysis/[id]" />
          <Stack.Screen name="map" />
          <Stack.Screen name="hotspots" />
          <Stack.Screen name="monitoring" />
          <Stack.Screen name="expert" />
          <Stack.Screen name="notifications" />
          <Stack.Screen name="help" />
          <Stack.Screen name="profile" />
          <Stack.Screen name="settings" />
          <Stack.Screen name="login" />
          <Stack.Screen name="register" />
        </Stack>
      </WorkspaceProvider>
    </SafeAreaProvider>
  );
}
