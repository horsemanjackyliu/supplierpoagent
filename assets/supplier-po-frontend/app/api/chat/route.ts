import { NextRequest, NextResponse } from 'next/server'

const AGENT_URL = process.env.NEXT_PUBLIC_AGENT_URL || 'https://27c30ede-2a17e47f.sap3eu12.c.run.ai.cloud.sap'

/**
 * POST /api/chat
 *
 * Proxies messages to the Joule Studio A2A agent.
 * The agent follows the Agent-to-Agent (A2A) protocol:
 *   POST /  with JSON body: { message: { parts: [{ text: "..." }] }, sessionId?: "..." }
 * Returns streaming SSE or a single JSON task response.
 */
export async function POST(req: NextRequest) {
  try {
    const { message, sessionId } = await req.json()

    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'message is required' }, { status: 400 })
    }

    // A2A protocol payload
    const a2aPayload = {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'tasks/send',
      params: {
        message: {
          role: 'user',
          parts: [{ type: 'text', text: message }],
        },
        ...(sessionId ? { sessionId } : {}),
      },
    }

    const agentRes = await fetch(`${AGENT_URL}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(a2aPayload),
    })

    if (!agentRes.ok) {
      const errorText = await agentRes.text()
      console.error('Agent error:', agentRes.status, errorText)
      return NextResponse.json(
        { error: `Agent returned ${agentRes.status}` },
        { status: 502 }
      )
    }

    const data = await agentRes.json()

    // Extract reply text from A2A task response
    // Shape: { result: { artifacts: [{ parts: [{ text: "..." }] }] } }
    //   or:  { result: { status: { message: { parts: [{ text: "..." }] } } } }
    let replyText = ''
    const result = data?.result

    if (result?.artifacts?.length) {
      const parts = result.artifacts[0]?.parts ?? []
      replyText = parts.map((p: { text?: string }) => p.text ?? '').join('\n')
    } else if (result?.status?.message?.parts?.length) {
      const parts = result.status.message.parts
      replyText = parts.map((p: { text?: string }) => p.text ?? '').join('\n')
    } else {
      replyText = JSON.stringify(data, null, 2)
    }

    const newSessionId = result?.sessionId ?? sessionId ?? null

    return NextResponse.json({ reply: replyText, sessionId: newSessionId })
  } catch (err) {
    console.error('Chat route error:', err)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
