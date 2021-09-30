package com.lightdestory.cryptosight;

import org.apache.kafka.common.serialization.Serdes;
import org.apache.kafka.streams.KafkaStreams;
import org.apache.kafka.streams.StreamsBuilder;
import org.apache.kafka.streams.StreamsConfig;
import org.apache.kafka.streams.Topology;
import org.apache.kafka.streams.KeyValue;
import org.json.JSONObject;
import java.util.Properties;
import java.util.Random;
import java.util.concurrent.CountDownLatch;

public class ConverterStream {

    final static String KAFKA_ADDRESS = "kafkaserver:9092";
    final static String RAW_TOPIC = "cryptocurrencies-raw";
    final static String PROCESSED_TOPIC = "cryptocurrencies";
    final static String APP_NAME = "CryptoSight";

    public static void main(String[] args) {
        // Creating the StreamBuilder instance
        final StreamsBuilder builder = new StreamsBuilder();
        // Assigning workload, parsing every KeyValue topic's message into a new one
        // Saving the new generated data into a second topic
        builder.<String, String>stream(RAW_TOPIC)
                .map((k, v) -> new KeyValue<>(k, generateCleanDataJSON(v)))
                .to(PROCESSED_TOPIC);
        // Initializing Stream
        final Topology topology = builder.build();
        final KafkaStreams streams = new KafkaStreams(topology, createProps());
        // Multithreading Counter
        final CountDownLatch latch = new CountDownLatch(1);
        // Attaching shutdown handler to catch control-c
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            // Closes the Stream
            streams.close();
            // Put the counter to 0, releasing the main thread from the freeze
            latch.countDown();
        }, String.format("streams-%s-shutdown", APP_NAME)));
        // Running the stream
        try {
            // Start the stream
            streams.start();
            // Put the main thread to a freeze state
            latch.await();
        } catch (Throwable e) {
            System.exit(1);
        }
        System.exit(0);
    }

    private static Properties createProps() {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, String.format("streams-%s", APP_NAME));
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, KAFKA_ADDRESS);
        props.put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        props.put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().getClass());
        return props;
    }

    private static String generateCleanDataJSON(String value) {
        JSONObject rawElement = new JSONObject(value);
        double current_price = rawElement.getDouble("current_price");
        double volume_usd = rawElement.getDouble("total_volume");
        Random randomizer = new Random();
        int offsetRandom = randomizer.nextInt(100);
        if(offsetRandom<=15) {
            double offset_price = Math.sqrt(current_price)*offsetRandom;
            double offset_volume = Math.sqrt(volume_usd)*offsetRandom;
            int mul = randomizer.nextInt(2)==0 ? 2 : -2;
            current_price+=(offset_price*mul);
            volume_usd+=(offset_volume*mul);
        }
        JSONObject cleanElement = new JSONObject();
        cleanElement.put("@timestamp", rawElement.getString("@timestamp"));
        cleanElement.put("coin", rawElement.getString("name"));
        cleanElement.put("market_cap", rawElement.getDouble("market_cap"));
        cleanElement.put("circulating_supply", rawElement.getDouble("circulating_supply"));
        cleanElement.put("current_price", current_price);
        cleanElement.put("total_volume", volume_usd);
        return cleanElement.toString();
    }
}
