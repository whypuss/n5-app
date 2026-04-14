package com.whypuss.n5app

import com.google.gson.annotations.SerializedName

/**
 * 統一的 Sentence 數據模型
 * 適用於 N1/N2/N3/N4/N5 所有級別
 */
data class Sentence(
    val id: Any = 0,
    // N1/N2/N5 有 japanese 字段；N3 無 japanese，需從 sequence 重建
    val japanese: String? = null,
    // N1/N2 有 character（漢字）→ 作為顯示主文字
    val character: String? = null,
    // N1/N2 有 word（詞語）→ N1 單字
    val word: String? = null,
    // N1/N2 有 mean（中文意思）→ 對應 meaning
    val mean: String? = null,
    // N3/N4/N5 有 translation（翻譯）
    val translation: String? = null,
    // 逐字拆解: [["漢字","讀音","羅馬字"], ...]
    val sequence: List<List<String>>? = null,
    // 解釋: [{"word": "詞", "mean": "意思", "pos": "詞性", "note": "備註"}, ...]
    val explanation: List<ExplanationItem>? = null,
    // N1/N2 有 source, category, tense
    val source: String? = null,
    val category: String? = null,
    val tense: String? = null
) {
    /** 顯示用主文字 */
    fun displayText(): String = when {
        // N5: explanation 有完整日語單字 → 顯示日語詞
        !explanation.isNullOrEmpty() && explanation[0].word.isNotEmpty() -> explanation[0].word
        // N2: explanation.word 空的 → 從 sequence 取日語字符
        !explanation.isNullOrEmpty() && explanation[0].word.isEmpty() && !sequence.isNullOrEmpty() ->
            sequence.joinToString("") { it.getOrNull(0) ?: "" }
        // 56 句全空的 → fallback 用羅馬字/平假名
        !explanation.isNullOrEmpty() && explanation[0].word.isEmpty() && sequence.isNullOrEmpty() ->
            explanation.getOrNull(1)?.word ?: explanation.getOrNull(1)?.mean ?: "—"
        !japanese.isNullOrEmpty() -> japanese
        !character.isNullOrEmpty() -> character
        !word.isNullOrEmpty() -> word
        sequence != null -> sequenceToJapanese()
        else -> "—"
    }

    /** 顯示用副文字（讀音/假名） */
    fun displaySub(): String = when {
        // N1/N2: 從 sequence 提取讀音
        !sequence.isNullOrEmpty() -> sequence.filter { it.size > 1 }
            .joinToString("") { it[1] }
        else -> ""
    }

    /** 顯示用意思 */
    fun displayMeaning(): String = when {
        // N5: 從 explanation 取中文意思
        !explanation.isNullOrEmpty() && explanation[0].mean.isNotEmpty() -> explanation[0].mean
        // N2: explanation.word 空的 56 句 → fallback 用 sequence
        !explanation.isNullOrEmpty() && explanation[0].word.isEmpty() && !sequence.isNullOrEmpty() ->
            sequence.filter { it.size > 1 }.joinToString("") { it[1] }
        !mean.isNullOrEmpty() -> mean          // N1/N2
        !translation.isNullOrEmpty() -> translation  // N3/N4/N5
        else -> ""
    }

    /** 從 sequence 重建日文句子 */
    private fun sequenceToJapanese(): String {
        if (sequence.isNullOrEmpty()) return "—"
        return sequence.joinToString("") { it.getOrNull(0) ?: "" }
    }

    /** 取得音頻文件名（如 n1/1.mp3） */
    fun audioFile(): String? {
        val num = when (id) {
            is Int -> id
            is String -> id.filter { it.isDigit() }.toIntOrNull()
            else -> null
        } ?: return null
        val level = when {
            !word.isNullOrEmpty() || (!character.isNullOrEmpty() && !japanese.isNullOrEmpty() && japanese!!.length < 15) -> "n1"
            !japanese.isNullOrEmpty() && japanese!!.length <= 10 -> "n5"
            else -> null
        } ?: return null
        return "audio/$level/$num.mp3"
    }
}

data class ExplanationItem(
    val word: String = "",
    val mean: String = "",
    val pos: String = "",
    val note: String = ""
)

data class DataWrapper(
    val sentences: List<Sentence>? = null
)
