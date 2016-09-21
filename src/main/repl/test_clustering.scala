import org.apache.spark.SparkConf
import org.apache.spark.mllib.clustering.StreamingKMeans
import org.apache.spark.mllib.linalg.Vectors
import org.apache.spark.mllib.regression.LabeledPoint
import org.apache.spark.streaming.{Seconds, StreamingContext}

val ssc = new StreamingContext(sc, Seconds(5))

val trainingData = ssc.textFileStream("hdfs://ec2-23-22-195-205.compute-1.amazonaws.com:9000/train/").map(Vectors.parse)
val testData = ssc.textFileStream("hdfs://ec2-23-22-195-205.compute-1.amazonaws.com:9000/test/").map(Vectors.parse)

val model = new StreamingKMeans().setK(100).setDecayFactor(0).setRandomCenters(38, 0.0)

model.trainOn(trainingData)
val outputDStream = model.predictOn(testData)
outputDStream.print()
outputDStream.foreachRDD(rdd => {
  if (!rdd.isEmpty){
    rdd.saveAsTextFile(List("hdfs://ec2-23-22-195-205.compute-1.amazonaws.com:9000/output/predict-", rdd.id).mkString(""))
  }
})

ssc.start()

/**
  * This needs to be updated for a streaming context.
  */
def distance(a: Vector, b: Vector) =
  math.sqrt(a.toArray.zip(b.toArray).map(p => p._1 - p._2).map(d => d*d).sum)

def distToCentroid(data: RDD[Vector], model: StreamingKMeansModel) = {
  /** @val clusters RDD[Int] Centroid indices for each record **/
  val clusters = data.map(record => (record, model.predict(record)))
  val distances = clusters.map(tup => (tup._1, distance(tup._1, model.clusterCenters(tup._2))))
}