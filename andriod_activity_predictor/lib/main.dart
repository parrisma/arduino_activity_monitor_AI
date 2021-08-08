import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:activity_manager/loading_page.dart';
import 'package:activity_manager/home_page.dart';

void main() async {
  runApp(ActivityManager());
}

class ActivityManager extends StatelessWidget {
  final String _title = 'Arduino BLE Activity Manager';

  /*
  We need to load the JSON config before starting the App. For this we
  need a FutureBuilder as the return from loading the config is async.
  So here we wait on loading the JSON and when done we build the
  landing page with the config cascaded as a parameter.
   */
  Widget _futureBuildMainPage(BuildContext context) {
    return Center(
      child: FutureBuilder<Map<String, dynamic>>(
        future: _loadJsonConfig(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.done) {
            return _buildHomePage(context, snapshot.data);
          } else {
            return _buildLoadingPage(context);
          }
        },
      ),
    );
  }

  /* Home page that shows all Bluetooth devices & allows connection with
     devices recognised as Arduino activity manager devices.
   */
  Widget _buildHomePage(BuildContext context, Map<String, dynamic> conf) {
    return MaterialApp(
      title: _title,
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: MyHomePage(title: _title, conf: conf),
    );
  }

  /* Shown while JSON config is being loaded via Future
   */
  Widget _buildLoadingPage(BuildContext context) {
    return MaterialApp(
      title: _title,
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: MyLoadingPage(title: _title),
    );
  }

  /* Build the main page after.
   */
  @override
  Widget build(BuildContext context) {
    return _futureBuildMainPage(context);
  }

  /* This App needs to share configuration with Python and Arduino sketches
     So we copy the common JSON file as an asset so it can be loaded and
     decoded here.
     This is async so we call it via a waiting call to FutureBuilder.
   */
  Future<Map<String, dynamic>> _loadJsonConfig() async {
    return await rootBundle
        .loadString("assets/json/conf.json")
        .then((jsonStr) => json.decode(jsonStr));
  }
}
