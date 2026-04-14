package com.whypuss.n5app

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import android.widget.Button

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        findViewById<Button>(R.id.btnN5).setOnClickListener { openList("n5", "N5") }
        findViewById<Button>(R.id.btnN4).setOnClickListener { openList("n4", "N4") }
        findViewById<Button>(R.id.btnN3).setOnClickListener { openList("n3", "N3") }
        findViewById<Button>(R.id.btnN2).setOnClickListener { openList("n2", "N2") }
        findViewById<Button>(R.id.btnN1).setOnClickListener { openList("n1", "N1") }
    }

    private fun openList(level: String, title: String) {
        startActivity(Intent(this, ListActivity::class.java).apply {
            putExtra("level", level)
            putExtra("title", title)
        })
    }
}
