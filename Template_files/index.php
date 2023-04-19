<head></head>
<body class="page_bg">
<?php
$relpath = explode('/',realpath('.'));
$username = end($relpath);
echo '<h1>'.$username.' reports listing</h1>' ;
$dir = opendir('./reports');
$sessions = array();
while ($sessions[] = readdir($dir));
closedir($dir);
sort($sessions);
foreach ($sessions as $session)
    if ($session!= "." && $session != ".." && $session != "") {
        echo '<div class="line"><h3 class="header">'.$session.':</h3> <a target="_blank" href="reports/'.$session.'/index.html">All</a> <a target="_blank" href="reports_good/'.$session.'/index.html">Good only</a></div>';
        }
?>
</body>
</html>

<style>
    .line {
        display: flex;
        width: 40vw;
        justify-content: space-between;
        align-items: center;
    }
    .header {
        margin: 0.5rem;
    }

</style>
