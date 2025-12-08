import 'package:flutter/material.dart';

class Validators {
  static FormFieldValidator<String> validateNotEmpty(String fieldName) {
    return (value) {
      if (value == null || value.isEmpty) {
        return '$fieldName不能为空';
      }
      return null;
    };
  }

  static FormFieldValidator<String> validatePassword() {
    return (value) {
      if (value == null || value.isEmpty) {
        return '密码不能为空';
      }
      if (value.length < 6) {
        return '密码长度不能少于6位';
      }
      return null;
    };
  }
}