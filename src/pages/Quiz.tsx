import { useState } from 'react'
import type { Questao } from '../types'

interface Props {
  disciplina: string
  questoes: Questao[]
  onFinalizar: (respostas: Record<string, string>) => void
  onVoltar: () => void
}

const LETRAS = ['A', 'B', 'C', 'D', 'E']

export default function Quiz({ disciplina, questoes, onFinalizar, onVoltar }: Props) {
  const [atual, setAtual] = useState(0)
  const [respostas, setRespostas] = useState<Record<string, string>>({})
  const [selecionada, setSelecionada] = useState<string | null>(null)

  const questao = questoes[atual]
  const total = questoes.length
  const progresso = Math.round((atual / total) * 100)

  function avancar() {
    if (!selecionada) return
    const novas = { ...respostas, [questao.id]: selecionada }
    setRespostas(novas)
    setSelecionada(null)
    if (atual + 1 >= total) {
      onFinalizar(novas)
    } else {
      setAtual(a => a + 1)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-8 px-4">
      {/* Header */}
      <div className="w-full max-w-2xl flex items-center justify-between mb-4">
        <button onClick={onVoltar} className="text-gray-400 hover:text-gray-600 text-sm">
          ← Voltar
        </button>
        <span className="text-gray-600 text-sm font-medium">{disciplina}</span>
        <span className="text-gray-400 text-sm">{atual + 1}/{total}</span>
      </div>

      {/* Barra de progresso */}
      <div className="w-full max-w-2xl h-1.5 bg-gray-200 rounded-full mb-8">
        <div
          className="h-1.5 bg-indigo-500 rounded-full transition-all duration-300"
          style={{ width: `${progresso}%` }}
        />
      </div>

      {/* Questão */}
      <div className="w-full max-w-2xl bg-white rounded-2xl border border-gray-200 p-6 mb-6 shadow-sm">
        <p className="text-xs text-gray-400 mb-3 uppercase tracking-wide">
          {questao.ano}/{questao.semestre} · Questão {questao.id.split('-').pop()}
        </p>
        <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">{questao.enunciado}</p>

        {questao.imagens.length > 0 && (
          <div className="mt-4 flex flex-col gap-3">
            {questao.imagens.map(img => (
              <img
                key={img}
                src={`${import.meta.env.BASE_URL}images/${img}`}
                alt="Figura da questão"
                className="max-w-full rounded-lg border border-gray-200"
              />
            ))}
          </div>
        )}
      </div>

      {/* Alternativas */}
      <div className="w-full max-w-2xl flex flex-col gap-3 mb-8">
        {LETRAS.filter(l => questao.alternativas[l]).map(letra => (
          <button
            key={letra}
            onClick={() => setSelecionada(letra)}
            className={`
              w-full text-left rounded-xl px-5 py-4 flex gap-4 items-start border transition-all
              ${selecionada === letra
                ? 'bg-indigo-50 border-indigo-400 ring-1 ring-indigo-300'
                : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'}
            `}
          >
            <span className={`font-bold text-sm mt-0.5 w-5 shrink-0 ${selecionada === letra ? 'text-indigo-600' : 'text-indigo-400'}`}>
              {letra}
            </span>
            <span className="text-gray-700 text-sm leading-relaxed">
              {questao.alternativas[letra]}
            </span>
          </button>
        ))}
      </div>

      {/* Botão avançar */}
      <button
        onClick={avancar}
        disabled={!selecionada}
        className={`
          px-10 py-3 rounded-xl font-semibold text-sm transition-all
          ${selecionada
            ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'}
        `}
      >
        {atual + 1 >= total ? 'Ver resultado' : 'Próxima →'}
      </button>
    </div>
  )
}
