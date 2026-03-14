<template>
  <el-container style="min-height: 100vh">
    <el-header>
      <el-menu mode="horizontal" :router="true" :default-active="$route.path">
        <el-menu-item index="/projects">Проекты</el-menu-item>
        <el-menu-item index="/selection">Отбор на семестр</el-menu-item>
        <el-menu-item index="/history">История</el-menu-item>
        <el-menu-item index="/dictionaries">Справочники</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>
