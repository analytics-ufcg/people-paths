# people-paths
Socio-spatio-temporal analysis of people movement from bus ticketing data from Curitiba's public bus system.
<h1>Execution Steps<h1>
<h5>Below, we will show all necessary steps for execute the scripts.<h5>

<ol>
  <li>
    <i>Index Ticketing data</i>
      <ol><li><h5>Execute the ticketing script: <i>python /local/joseiscj/workspace/people-paths/python/scripts/ticketing/index-ticketing-data.py</i> (for examplo)<h5></li>
      <li><h5>Pass the directory as parameter: <i>/local/joseiscj/data/ticketing-data/raw</i> (for examplo)<h5></li>
      <li><h5>pass the output's directory as parameter: <i>/local/joseiscj/data/ticketing-data/indexed</i> (for examplo)<h5></li>
      <li><h5>indicate the datas begin and end dates: <i>2017-05-01 2017-07-30</i> (for examplo)<h5></li>
      </ol>
      
  <li>
    <i>Match GPS points to GTFS trips (BULMA) - This is the execution of a spark job</i>
      <ol><li><h5><i>/opt/spark/bin/spark-submit</i> (for examplo)<h5></li>
      <li><h5><i> --class BULMA.MatchingRoutesShapeGPS</i> (for examplo)<h5></li>
      <li><h5><i>--master spark://10.11.4.10:7077 (for examplo)<h5></li>
      <li><h5><i>--driver-memory 2G (for examplo)<h5></li>
      <li><h5><i>--executor-memory 2700m (for examplo)<h5></li>
      <li><h5>/home/ubuntu/LQD/BulmaBuste.jar (for examplo)<h5></li>
      <li><h5>/user/ubuntu/inputs/shapesCuritiba.csv (for examplo)<h5></li>
      <li><h5>/user/ubuntu/inputs/GPS/junho/ (for examplo)<h5></li>
      <li><h5>/user/ubuntu/outputs/BULMA/ 8 (for examplo)</li>
      </ol>
  <li>
     <i>Match Trips to Ticketing data (BUSTE) - This is the execution of a spark job</i>
      <ol><li><h5><i>/opt/spark/bin/spark-submit (for examplo)<h5></li>
      <li><h5><i> --class recordLinkage.BUSTEstimationV3 (for examplo)<h5></li>
      <li><h5><i> --master spark://10.11.4.10:7077 (for examplo)<h5></li>
      <li><h5><i> --driver-memory 2G (for examplo)<h5></li>
      <li><h5><i>--executor-memory 2700m (for examplo)<h5></li>
      <li><h5>/home/ubuntu/LQD/BulmaBuste.jar (for examplo)<h5></li>
      <li><h5>/user/ubuntu/outputs/BULMA-maio/ (for examplo)<h5></li>
      <li><h5>/user/ubuntu/inputs/shapesCuritiba.csv (for examplo)<h5></li>
      <li><h5>/user/ubuntu/inputs/stopsCuritiba.csv (for examplo)</li>
      <li><h5>/user/ubuntu/inputs/tickets/ (for examplo)</li>
      <li><h5>/user/ubuntu/outputs/BUSTE-maio/ 8 (for examplo)</li>
      </ol>
  <li>
    <i>Enhance Buste data</i>
      <ol><li><h5>Execute the buste script: <i>python /local/joseiscj/workspace/people-paths/python/scripts/buste/enhace-buste-data.py</i> (for examplo)<h5></li>
      <li><h5>Pass the directory as parameter: <i>/local/joseiscj/data/BUSTE/raw</i> (for examplo)<h5></li>
      <li><h5>pass the ticketing's indexed directory as parameter: <i>/local/joseiscj/data/ticketing-data/indexed</i> (for examplo)<h5></li>
      <li><h5>pass the output's directory as parameter: <i>/local/joseiscj/data/enhanced_buste</i> (for examplo)<h5></li>
      <li><h5>indicate the datas begin and end dates: <i>2017-05-01 2017-07-30</i> (for examplo)<h5></li>
      <li><h5>indicate the terminals translation table: <i>/local/joseiscj/data/line-000-terminals-translation-table.csv</i> (for examplo)<h5></li>
      <li><h5>indicate the GTFS's directory: <i>/local/joseiscj/data/gtfs</i> (for examplo)<h5></li>
      </ol>
  <li>
  <li>
  <li>
  <li>
  <li>
  <li>
  <li>
  <li>
  <li>
  <li>

  
