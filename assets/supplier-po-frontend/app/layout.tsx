import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Supplier PO Assistant',
  description: 'AI-powered purchase order self-service for suppliers',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
