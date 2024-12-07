use actix_web::{rt, web, App, Error, HttpRequest, HttpResponse, HttpServer};
use actix_ws::AggregatedMessage;
use futures_util::StreamExt as _;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

struct MessageStats {
    count: usize,
    total_size: usize,
    last_logged: Instant,
}
impl MessageStats {
    fn new() -> Self {
        Self {
            count: 0,
            total_size: 0,
            last_logged: Instant::now(),
        }
    }

    fn update(&mut self, message_size: usize) {
        self.count += 1;
        self.total_size += message_size;

        // Если прошло больше 1 секунды с последнего логирования, логируем и сбрасываем статистику
        if self.last_logged.elapsed() >= Duration::from_secs(1) {
            println!(
                "За последнюю секунду: сообщений: {}, общий размер: {} байт",
                self.count, self.total_size
            );
            self.count = 0;
            self.total_size = 0;
            self.last_logged = Instant::now();
        }
    }
}

async fn handle_binary_message(stats: Arc<Mutex<MessageStats>>, bin: Vec<u8>) {
    let mut stats = stats.lock().unwrap();
    stats.update(bin.len());
}

async fn echo(req: HttpRequest, stream: web::Payload) -> Result<HttpResponse, Error> {
    let (res, mut session, stream) = actix_ws::handle(&req, stream)?;

    let mut stream = stream
        .aggregate_continuations()
        // aggregate continuation frames up to 1MiB
        .max_continuation_size(2_usize.pow(20));

    let stats = Arc::new(Mutex::new(MessageStats::new()));

    // start task but don't wait for it
    rt::spawn(async move {
        // receive messages from websocket
        while let Some(msg) = stream.next().await {
            match msg {
                Ok(AggregatedMessage::Binary(bin)) => {
                    handle_binary_message(stats.clone(), bin.to_vec()).await;
                }

                Ok(AggregatedMessage::Ping(msg)) => {
                    // respond to PING frame with PONG frame
                    session.pong(&msg).await.unwrap();
                }

                _ => {}
            }
        }
    });

    // respond immediately with response connected to WS session
    Ok(res)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("Start WS server");
    HttpServer::new(|| App::new().route("/", web::get().to(echo)))
        .bind(("127.0.0.1", 8000))?
        .run()
        .await
}