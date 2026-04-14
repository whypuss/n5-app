package com.whypuss.n5app

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.gson.Gson

class ListActivity : AppCompatActivity() {
    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: ItemAdapter
    private var level: String = "n5"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_list)

        level = intent.getStringExtra("level") ?: "n5"
        title = "N5/N4/N3/N2/N1 列表"

        recyclerView = findViewById(R.id.recyclerView)
        recyclerView.layoutManager = LinearLayoutManager(this)
        adapter = ItemAdapter()
        recyclerView.adapter = adapter

        loadData()
    }

    private fun loadData() {
        val filename = when (level) {
            "n1" -> "data/n1-data.json"
            "n2" -> "data/n2-data.json"
            "n3" -> "data/n3-v2-data.json"
            "n4" -> "data/n4-v2-data.json"
            "n5" -> "data/n5-v2-data.json"
            else -> "data/n5-v2-data.json"
        }

        try {
            val json = assets.open(filename).bufferedReader().use { it.readText() }
            val wrapper = Gson().fromJson(json, DataWrapper::class.java)
            val items = wrapper.sentences ?: emptyList()
            adapter.submitList(items)
        } catch (e: Exception) {
            android.widget.Toast.makeText(this, "加載失敗: ${e.message}", android.widget.Toast.LENGTH_LONG).show()
        }
    }

    inner class ItemAdapter : RecyclerView.Adapter<ItemAdapter.ViewHolder>() {
        private var items: List<Sentence> = emptyList()

        fun submitList(list: List<Sentence>) {
            items = list
            notifyDataSetChanged()
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
            val view = LayoutInflater.from(parent.context)
                .inflate(R.layout.item_row, parent, false)
            return ViewHolder(view)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val item = items[position]
            holder.bind(item, position + 1)
            holder.itemView.setOnClickListener {
                startActivity(Intent(this@ListActivity, DetailActivity::class.java).apply {
                    putExtra("level", level)
                    putExtra("position", position)
                    putExtra("title", "${intent.getStringExtra("title") ?: ""} #${position + 1}")
                })
            }
        }

        override fun getItemCount() = items.size

        inner class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
            private val numText: TextView = itemView.findViewById(R.id.numText)
            private val mainText: TextView = itemView.findViewById(R.id.mainText)
            private val subText: TextView = itemView.findViewById(R.id.subText)

            fun bind(item: Sentence, num: Int) {
                numText.text = "#$num"
                mainText.text = item.displayText()
                subText.text = item.displayMeaning()
            }
        }
    }
}
