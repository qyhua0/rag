<template>
  <svg :class="['animate-spin', $attrs.class || 'w-5 h-5 text-primary-500']"
    fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
  </svg>
</template>
