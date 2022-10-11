<head></head>
<body class="page_bg">
<?php
// Read directory, spit out links
$relpath = str_replace("/data/html","",realpath('.'));
$username = str_replace("/data/html/reports/","",realpath('.'));
echo $username." reports listing <br>";
if ($handle = opendir('./reports')) {
    while (false !== ($entry = readdir($handle))) {
        if ($entry != "." && $entry != "..") {
            echo '<a href="'.$relpath.'/reports/'.$entry.'/index.html">'.$entry.'</a><br>';
        }
    }
    closedir($handle);
}
if ($handle = opendir('./Scipion')) {
    while (false !== ($entry = readdir($handle))) {
        if ($entry != "." && $entry != "..") {
            echo '<a href="'.$relpath.'/reports/'.$entry.'/index.html">'.$entry.'</a><br>';
        }
    }
    closedir($handle);
}
?>
</body>
</html>
