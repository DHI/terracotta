import React, {
	useState,
	useEffect,
	useCallback,
	FC,
	MouseEventHandler,
	MouseEvent,
} from "react";
import Handle from "./Handle";

interface Props {
	boxWidth: number;
	onDrag: (w: number) => void;
	minSize?: number;
	minMapSize?: number;
}

const VerticalHandle: FC<Props> = ({
	boxWidth,
	onDrag,
	minSize = 0,
	minMapSize = (20 / 100) * window.innerWidth,
}) => {
	const [isDragging, setIsDragging] = useState(false);
	const [initialWidth, setInitialWidth] = useState(minSize * 2);

	const handleMouseMove = useCallback(
		(e: MouseEvent<HTMLDivElement>) => {
			const windowWidth = window.innerWidth;
			let w =
				e.clientX < minMapSize
					? windowWidth - minMapSize
					: windowWidth - e.clientX;

			w = w < minSize ? 0 : w;
			onDrag(w);
		},
		[onDrag, minMapSize, minSize],
	) as MouseEventHandler<HTMLDivElement>;

	const handleMouseDown = useCallback(
		(e: MouseEvent<HTMLDivElement>) => {
			setIsDragging(true);
			const w = window.innerWidth - e.clientX;
			setInitialWidth(initialWidth < minSize ? minSize : w);
		},
		[initialWidth, minSize],
	) as MouseEventHandler<HTMLDivElement>;

	const handleMouseUp = useCallback(() => {
		setIsDragging(false);
	}, []);

	useEffect(() => {
		const add = () => {
			window.addEventListener("mousedown", handleMouseDown as any);
			window.addEventListener("mousemove", handleMouseMove as any);
			window.addEventListener("mouseup", handleMouseUp);
		};

		const remove = () => {
			window.removeEventListener("mousedown", handleMouseDown as any);
			window.removeEventListener("mousemove", handleMouseMove as any);
			window.removeEventListener("mouseup", handleMouseUp);
		};

		if (isDragging) {
			add();
		} else {
			remove();
		}

		return remove;
	}, [isDragging, handleMouseMove, handleMouseDown, handleMouseUp]);

	return (
		<Handle
			onMouseDown={handleMouseDown}
			onMouseUp={handleMouseUp}
			isCollapsed={boxWidth < 10}
			onClickExpand={() => onDrag((30 / 100) * window.innerWidth)}
		/>
	);
};

export default VerticalHandle;
