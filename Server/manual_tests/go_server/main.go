package main

import (
    "fmt"
    "log"
    "net/http"
    "github.com/gorilla/websocket"
    "time"
)

var (
    upgrader = websocket.Upgrader{
        CheckOrigin: func(r *http.Request) bool {
            return true
        },
//        ReadLimit:  10 * 1024 * 1024,  // Ограничение на чтение сообщений (10MB)
//        WriteLimit: 10 * 1024 * 1024,  // Ограничение на запись сообщений (10MB)
    }
    packetCount   = 0
    maxPacketSize = 0
)

func handleWebSocket(w http.ResponseWriter, r *http.Request) {
    conn, err := upgrader.Upgrade(w, r, nil)
    if err != nil {
        log.Println("Error upgrading connection:", err)
        return
    }
    defer conn.Close()

    conn.SetReadLimit(100 * 1024 * 1024) // Ограничение на чтение сообщений (10MB)
//    conn.SetWriteLimit(10 * 1024 * 1024) // Ограничение на запись сообщений (10MB)

    fmt.Println("New client connected")

    startTime := time.Now()

    // Канал для пинга
    ticker := time.NewTicker(10 * time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-ticker.C: // Пинг каждую секунду
            err := conn.WriteMessage(websocket.TextMessage, []byte("ping"))
            if err != nil {
                log.Println("Error sending ping:", err)
                return
            }
            fmt.Println("Sent ping to client")

        default:
            messageType, p, err := conn.ReadMessage()
            if err != nil {
                log.Println("Error reading message:", err)
                fmt.Println("Client disconnected")
                return
            }

            packetCount++
            if len(p) > maxPacketSize {
                maxPacketSize = len(p)
            }

            // Вычисление за 1 секунду
            if time.Since(startTime) > time.Second {
                fmt.Printf("Received %d packets in the last second\n", packetCount)
                fmt.Printf("Max packet size in the last second: %d bytes\n", maxPacketSize)
                packetCount = 0
                maxPacketSize = 0
                startTime = time.Now()
            }

            // Эхо-сообщение
            if messageType == websocket.TextMessage || messageType == websocket.BinaryMessage {
//                conn.WriteMessage(messageType, p)
            }
        }
    }
}

func main() {
    http.HandleFunc("/", handleWebSocket)

    // Периодически выводим информацию о том, что сервер жив
    go func() {
        ticker := time.NewTicker(10 * time.Second)
        defer ticker.Stop()
        for {
            select {
            case <-ticker.C:
                fmt.Println("Server is still alive")
            }
        }
    }()

    fmt.Println("WebSocket server started at ws://0.0.0.0:8000")
    log.Fatal(http.ListenAndServe(":8000", nil))
}

