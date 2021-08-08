import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';

class MyLoadingPage extends StatefulWidget {
  MyLoadingPage({Key key, this.title}) : super(key: key);
  final String title;

  @override
  _MyLoadingPageState createState() => _MyLoadingPageState(title: title);
}

class _MyLoadingPageState extends State<MyLoadingPage> {
  _MyLoadingPageState({this.title});

  final String title;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: Text("Loading"),
        ),
        body: _buildLoadingPage(title),
      );

  /* View to show while loading configuration
   */
  Widget _buildLoadingPage(String title) {
    return MaterialApp(
      title: title,
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: Column(
        children: [
          Divider(height: 20, thickness: 2, indent: 20, endIndent: 20),
          Container(
            height: 300,
            child: Image(image: AssetImage("assets/images/arduino.png")),
          ),
          Divider(height: 20, thickness: 2, indent: 20, endIndent: 20),
          Container(
            child: CircularProgressIndicator(
              backgroundColor: Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
}
