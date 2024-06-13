<script lang="ts">
	export let position: string = 'left'; // Can be "left" or "right"
	export let width: string = '200px';
</script>

<div class="side-panel {position}" style="--width: {width}">
	<slot></slot>
</div>

<style>
	.side-panel {
		width: var(--width);
		height: calc(100% - 100px); /* Subtracting the height of the top menu */
		background-color: #f4f4f4;
		position: fixed;
		top: 100px;
		transition:
			left 0.3s,
			right 0.3s;
	}
	.side-panel.left {
		left: 0;
	}
	.side-panel.right {
		right: 0;
	}
</style>
