import { useNavigation } from "react-router";

/** Barra fina no topo enquanto uma navegação ou envio está em andamento. */
export function PendingBar() {
  const navigation = useNavigation();
  if (navigation.state === "idle") return null;
  return (
    <div className="fixed inset-x-0 top-0 z-50 h-0.5 overflow-hidden bg-blue-100" role="progressbar" aria-label="Carregando">
      <div className="h-full w-1/3 animate-[barra_1s_ease-in-out_infinite] bg-blue-600" />
    </div>
  );
}
