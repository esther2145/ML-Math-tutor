export interface VerificationResult {
  status: 'passed' | 'failed' | 'not_checked'
  check: string
  expected_result?: string | null
  reason?: string
  reference_status?: 'passed' | 'failed' | 'not_checkable'
  invalid_references?: string[]
  uncited_claim_count?: number
  refinement_attempts?: number
}

export interface RetrievedMaterial {
  id?: number | string | null
  score?: number | null
  topic?: string | null
  grade?: number | null
  title?: string | null
  content?: string | null
  country_code?: string | null
  curriculum_name?: string | null
  curriculum_version?: string | null
  source_title?: string | null
  source_url?: string | null
  source_page?: string | null
  source_license?: string | null
  source_status?: string | null
}

export interface RetrievalTrace {
  vector_search?: {
    status?: string
    filters?: Record<string, unknown>
    minimum_score?: number | null
    hit_count?: number
    hits?: RetrievedMaterial[]
  }
  graph_lookup?: {
    status?: string
    query_topic?: string | null
    node_id?: string | null
    topic?: string | null
    provenance_status?: string
  }
}

export interface TutorResponse {
  answer: string
  verification?: VerificationResult
  retrieved_materials?: RetrievedMaterial[]
  retrieval_trace?: RetrievalTrace
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isOptionalString(
  record: Record<string, unknown>,
  key: string,
): boolean {
  return !(key in record) || record[key] === null || typeof record[key] === 'string'
}

function isOptionalNumber(
  record: Record<string, unknown>,
  key: string,
): boolean {
  return !(key in record) || record[key] === null || typeof record[key] === 'number'
}

function isRetrievedMaterial(value: unknown): value is RetrievedMaterial {
  if (!isRecord(value)) {
    return false
  }

  const validId =
    !('id' in value) ||
    value.id === null ||
    typeof value.id === 'number' ||
    typeof value.id === 'string'

  return (
    validId &&
    isOptionalNumber(value, 'score') &&
    isOptionalNumber(value, 'grade') &&
    isOptionalString(value, 'topic') &&
    isOptionalString(value, 'title') &&
    isOptionalString(value, 'content') &&
    isOptionalString(value, 'country_code') &&
    isOptionalString(value, 'curriculum_name') &&
    isOptionalString(value, 'curriculum_version') &&
    isOptionalString(value, 'source_title') &&
    isOptionalString(value, 'source_url') &&
    isOptionalString(value, 'source_page') &&
    isOptionalString(value, 'source_license') &&
    isOptionalString(value, 'source_status')
  )
}

function isVerificationResult(value: unknown): value is VerificationResult {
  if (!isRecord(value)) {
    return false
  }

  const validReferenceStatus =
    !('reference_status' in value) ||
    value.reference_status === 'passed' ||
    value.reference_status === 'failed' ||
    value.reference_status === 'not_checkable'
  const validInvalidReferences =
    !('invalid_references' in value) ||
    (Array.isArray(value.invalid_references) &&
      value.invalid_references.every(
        (reference) => typeof reference === 'string',
      ))

  return (
    (value.status === 'passed' ||
      value.status === 'failed' ||
      value.status === 'not_checked') &&
    typeof value.check === 'string' &&
    isOptionalString(value, 'expected_result') &&
    isOptionalString(value, 'reason') &&
    validReferenceStatus &&
    validInvalidReferences &&
    (!('uncited_claim_count' in value) ||
      typeof value.uncited_claim_count === 'number') &&
    (!('refinement_attempts' in value) ||
      typeof value.refinement_attempts === 'number')
  )
}

function isRetrievalTrace(value: unknown): value is RetrievalTrace {
  if (!isRecord(value)) {
    return false
  }

  const vectorSearch = value.vector_search
  const graphLookup = value.graph_lookup
  const validVectorSearch =
    vectorSearch === undefined ||
    (isRecord(vectorSearch) &&
      isOptionalString(vectorSearch, 'status') &&
      isOptionalNumber(vectorSearch, 'minimum_score') &&
      (!('hit_count' in vectorSearch) ||
        typeof vectorSearch.hit_count === 'number') &&
      (!('filters' in vectorSearch) || isRecord(vectorSearch.filters)) &&
      (!('hits' in vectorSearch) ||
        (Array.isArray(vectorSearch.hits) &&
          vectorSearch.hits.every(isRetrievedMaterial))))
  const validGraphLookup =
    graphLookup === undefined ||
    (isRecord(graphLookup) &&
      isOptionalString(graphLookup, 'status') &&
      isOptionalString(graphLookup, 'query_topic') &&
      isOptionalString(graphLookup, 'node_id') &&
      isOptionalString(graphLookup, 'topic') &&
      isOptionalString(graphLookup, 'provenance_status'))

  return validVectorSearch && validGraphLookup
}

export async function askTutor(
  question: string,
  learnerGrade: number,
): Promise<TutorResponse> {
  let response: Response

  try {
    response = await fetch('/api/tutor/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        learner_grade: learnerGrade,
      }),
    })
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        'Could not reach the tutor API. Check that FastAPI is running at http://127.0.0.1:8000.',
      )
    }
    throw error
  }

  const data: unknown = await response.json().catch(() => null)

  if (!response.ok) {
    const detail =
      isRecord(data) && typeof data.detail === 'string'
        ? data.detail
        : `The tutor API returned an error (${response.status}).`
    throw new Error(detail)
  }

  if (!isRecord(data) || typeof data.answer !== 'string') {
    throw new Error('The tutor API returned an invalid response.')
  }

  const result: TutorResponse = { answer: data.answer }

  if (data.verification !== undefined && data.verification !== null) {
    if (!isVerificationResult(data.verification)) {
      throw new Error('The tutor API returned invalid verification data.')
    }
    result.verification = data.verification
  }

  if (data.retrieved_materials !== undefined) {
    if (
      !Array.isArray(data.retrieved_materials) ||
      !data.retrieved_materials.every(isRetrievedMaterial)
    ) {
      throw new Error('The tutor API returned invalid retrieved materials.')
    }
    result.retrieved_materials = data.retrieved_materials
  }

  if (data.retrieval_trace !== undefined && data.retrieval_trace !== null) {
    if (!isRetrievalTrace(data.retrieval_trace)) {
      throw new Error('The tutor API returned an invalid retrieval trace.')
    }
    result.retrieval_trace = data.retrieval_trace
  }

  return result
}
