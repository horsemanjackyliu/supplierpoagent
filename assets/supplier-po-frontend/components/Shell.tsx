import { Package } from 'lucide-react'

export default function Shell() {
  return (
    <header className="sap-shell">
      {/* SAP logo area */}
      <div className="flex items-center gap-2 border-r border-white/20 pr-4">
        <span className="text-white font-bold text-lg tracking-wide">SAP</span>
      </div>

      {/* App title */}
      <div className="flex items-center gap-2 flex-1">
        <Package className="text-white w-5 h-5" />
        <span className="text-white text-sm font-medium">Supplier PO Assistant</span>
      </div>

      {/* Right slot */}
      <div className="flex items-center gap-3">
        <span className="text-white/60 text-xs hidden sm:block">
          Powered by SAP S/4HANA Cloud
        </span>
        <div className="w-7 h-7 rounded-full bg-sap-blue flex items-center justify-center border border-white/30">
          <span className="text-white text-xs font-semibold">S</span>
        </div>
      </div>
    </header>
  )
}
