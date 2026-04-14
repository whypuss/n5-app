package com.whypuss.n5app

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

class DetailActivity : AppCompatActivity() {
    private lateinit var sentence: Sentence
    private lateinit var seqAdapter: SeqAdapter
    private lateinit var wordAdapter: WordAdapter
    private var audioData: ByteArray? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_detail)

        val level = intent.getStringExtra("level") ?: "n5"
        val position = intent.getIntExtra("position", 0)
        title = intent.getStringExtra("title") ?: "詳情"

        seqAdapter = SeqAdapter()
        findViewById<RecyclerView>(R.id.seqRecycler).apply {
            layoutManager = LinearLayoutManager(this@DetailActivity)
            adapter = seqAdapter
        }

        wordAdapter = WordAdapter()
        findViewById<RecyclerView>(R.id.wordRecycler).apply {
            layoutManager = LinearLayoutManager(this@DetailActivity)
            adapter = wordAdapter
        }

        loadData(level, position)
    }

    private fun loadData(level: String, position: Int) {
        val filename = when (level) {
            "n1" -> "data/n1-data.json"
            "n2" -> "data/n2-data.json"
            "n3" -> "data/n3-v2-data.json"
            "n4" -> "data/n4-v2-data.json"
            "n5" -> "data/n5-v2-data.json"
            else -> "data/n5-v2-data.json"
        }

        lifecycleScope.launch {
            try {
                val json = withContext(Dispatchers.IO) {
                    assets.open(filename).bufferedReader().use { it.readText() }
                }
                val wrapper = Gson().fromJson(json, DataWrapper::class.java)
                val items = wrapper.sentences ?: emptyList()

                if (position < items.size) {
                    sentence = items[position]
                    displaySentence()
                    loadAudio(level, position + 1)
                }
            } catch (e: Exception) {
                Toast.makeText(this@DetailActivity, "加載失敗: ${e.message}", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun displaySentence() {
        findViewById<TextView>(R.id.japaneseText).text = sentence.displayText()
        findViewById<TextView>(R.id.readingText).text = sentence.displaySub()
        findViewById<TextView>(R.id.meaningText).text = sentence.displayMeaning()

        val meta = listOfNotNull(sentence.category, sentence.tense).joinToString(" · ")
        findViewById<TextView>(R.id.metaText).text = meta

        // 詞彙表（explanation）
        if (!sentence.explanation.isNullOrEmpty()) {
            findViewById<View>(R.id.wordSection).visibility = View.VISIBLE
            wordAdapter.submitList(sentence.explanation)
        } else {
            findViewById<View>(R.id.wordSection).visibility = View.GONE
        }

        // 逐字拆解
        if (!sentence.sequence.isNullOrEmpty()) {
            findViewById<View>(R.id.seqSection).visibility = View.VISIBLE
            seqAdapter.submitList(sentence.sequence)
        } else {
            findViewById<View>(R.id.seqSection).visibility = View.GONE
        }

        // Play
        findViewById<Button>(R.id.playBtn).setOnClickListener { playAudio() }
    }

    private fun loadAudio(level: String, num: Int) {
        val audioFile = when (level) {
            "n1" -> "audio/n1/$num.mp3"
            "n5" -> "audio/n5/$num.mp3"
            else -> null
        }

        if (audioFile == null) {
            findViewById<TextView>(R.id.audioStatus).text = "無音頻"
            findViewById<Button>(R.id.playBtn).isEnabled = false
            return
        }

        lifecycleScope.launch(Dispatchers.IO) {
            try {
                audioData = assets.open(audioFile).use { it.readBytes() }
                withContext(Dispatchers.Main) {
                    findViewById<Button>(R.id.playBtn).isEnabled = true
                    findViewById<TextView>(R.id.audioStatus).text = "音頻就緒"
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    findViewById<TextView>(R.id.audioStatus).text = "無音頻"
                    findViewById<Button>(R.id.playBtn).isEnabled = false
                }
            }
        }
    }

    private fun playAudio() {
        val data = audioData ?: return
        lifecycleScope.launch(Dispatchers.IO) {
            try {
                val pcm = decodeMp3(data)
                playPcm(pcm)
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    Toast.makeText(this@DetailActivity, "播放失敗: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun decodeMp3(mp3Data: ByteArray): ShortArray {
        val tempFile = File(cacheDir, "temp.mp3")
        tempFile.writeBytes(mp3Data)

        val extractor = MediaExtractor()
        extractor.setDataSource(tempFile.absolutePath)

        var trackIndex = -1
        for (i in 0 until extractor.trackCount) {
            val format = extractor.getTrackFormat(i)
            val mime = format.getString(MediaFormat.KEY_MIME)
            if (mime?.startsWith("audio/") == true) {
                trackIndex = i
                break
            }
        }
        if (trackIndex == -1) throw Exception("No audio track")
        extractor.selectTrack(trackIndex)

        val format = extractor.getTrackFormat(trackIndex)
        val sampleRate = format.getInteger(MediaFormat.KEY_SAMPLE_RATE)
        val channelCount = format.getInteger(MediaFormat.KEY_CHANNEL_COUNT)

        val codec = MediaCodec.createDecoderByType("audio/mpeg")
        codec.configure(format, null, null, 0)
        codec.start()

        val bufferInfo = MediaCodec.BufferInfo()
        val pcmList = mutableListOf<Short>()
        val TIMEOUT_US = 10000L

        // Feed input
        var inputDone = false
        while (!inputDone) {
            val inputIndex = codec.dequeueInputBuffer(TIMEOUT_US)
            if (inputIndex >= 0) {
                val inputBuffer = codec.getInputBuffer(inputIndex)!!
                val sampleSize = extractor.readSampleData(inputBuffer, 0)
                if (sampleSize < 0) {
                    codec.queueInputBuffer(inputIndex, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM)
                    inputDone = true
                } else {
                    codec.queueInputBuffer(inputIndex, 0, sampleSize, extractor.sampleTime, 0)
                    extractor.advance()
                }
            }
        }

        // Drain output
        var outputDone = false
        while (!outputDone) {
            val outputIndex = codec.dequeueOutputBuffer(bufferInfo, TIMEOUT_US)
            when {
                outputIndex == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {}
                outputIndex >= 0 -> {
                    val outputBuffer = codec.getOutputBuffer(outputIndex)!!
                    val shortBuffer = outputBuffer.asShortBuffer()
                    val shorts = ShortArray(shortBuffer.remaining())
                    shortBuffer.get(shorts)
                    pcmList.addAll(shorts.toList())
                    codec.releaseOutputBuffer(outputIndex, false)
                    if (bufferInfo.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) {
                        outputDone = true
                    }
                }
            }
        }

        codec.stop()
        codec.release()
        extractor.release()
        tempFile.delete()

        return pcmList.toShortArray()
    }

    private fun playPcm(pcmData: ShortArray) {
        val SAMPLE_RATE = 44100
        val minBuffer = AudioTrack.getMinBufferSize(
            SAMPLE_RATE,
            AudioFormat.CHANNEL_OUT_MONO,
            AudioFormat.ENCODING_PCM_16BIT
        )

        val track = AudioTrack.Builder()
            .setAudioAttributes(AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build())
            .setAudioFormat(AudioFormat.Builder()
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setSampleRate(SAMPLE_RATE)
                .setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build())
            .setBufferSizeInBytes(minBuffer.coerceAtLeast(pcmData.size * 2))
            .setTransferMode(AudioTrack.MODE_STREAM).build()

        track.play()
        track.write(pcmData, 0, pcmData.size)
        track.stop()
        track.release()
    }

    inner class SeqAdapter : RecyclerView.Adapter<SeqAdapter.ViewHolder>() {
        private var sequence: List<List<String>> = emptyList()
        fun submitList(list: List<List<String>>) {
            sequence = list
            notifyDataSetChanged()
        }
        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) =
            ViewHolder(LayoutInflater.from(parent.context).inflate(R.layout.seq_row, parent, false))
        override fun onBindViewHolder(holder: ViewHolder, position: Int) = holder.bind(sequence[position])
        override fun getItemCount() = sequence.size
        inner class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
            private val charText: TextView = itemView.findViewById(R.id.seqChar)
            private val readingText: TextView = itemView.findViewById(R.id.seqReading)
            fun bind(item: List<String>) {
                charText.text = item.getOrNull(0) ?: ""
                readingText.text = item.getOrNull(1) ?: ""
            }
        }
    }

    inner class WordAdapter : RecyclerView.Adapter<WordAdapter.ViewHolder>() {
        private var words: List<ExplanationItem> = emptyList()
        fun submitList(list: List<ExplanationItem>) {
            words = list
            notifyDataSetChanged()
        }
        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int) =
            ViewHolder(LayoutInflater.from(parent.context).inflate(R.layout.word_row, parent, false))
        override fun onBindViewHolder(holder: ViewHolder, position: Int) = holder.bind(words[position])
        override fun getItemCount() = words.size
        inner class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
            private val wordText: TextView = itemView.findViewById(R.id.wordText)
            private val posText: TextView = itemView.findViewById(R.id.posText)
            private val meanText: TextView = itemView.findViewById(R.id.meanText)
            private val noteText: TextView = itemView.findViewById(R.id.noteText)
            fun bind(item: ExplanationItem) {
                wordText.text = item.word
                posText.text = item.pos
                meanText.text = item.mean
                noteText.text = item.note
                noteText.visibility = if (item.note.isNotEmpty()) View.VISIBLE else View.GONE
            }
        }
    }
}
