'use client'

import Chat from '@/components/Chat'
import Shell from '@/components/Shell'

export default function Home() {
  return (
    <div className="flex flex-col h-screen">
      <Shell />
      <main className="flex-1 overflow-hidden flex flex-col">
        <Chat />
      </main>
    </div>
  )
}
