import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useState,
} from 'react'

interface DropdownProps {
  items: string[];
  command: (arg: { id: string }) => void;
}

interface DropdownRef {
  onKeyDown: (arg: { event: KeyboardEvent }) => boolean;
}

const Dropdown = forwardRef<DropdownRef, DropdownProps>((props, ref) => {
  const [selectedIndex, setSelectedIndex] = useState(0)

  const selectItem = (index: number) => {
    const item = props.items[index]

    if (item) {
      props.command({ id: item })
    }
  }

  const upHandler = () => {
    setSelectedIndex((selectedIndex + props.items.length - 1) % props.items.length)
  }

  const downHandler = () => {
    setSelectedIndex((selectedIndex + 1) % props.items.length)
  }

  const enterHandler = (e: any) => {
    e.stopImmediatePropagation();
    e.preventDefault();
    e.stopPropagation();
    selectItem(selectedIndex)
  }

  useEffect(() => setSelectedIndex(0), [props.items])

  useImperativeHandle(ref, () => ({
    onKeyDown: ({ event }: { event: any }) => {
      if (event.key === 'ArrowUp') {
        upHandler()
        return true
      }

      if (event.key === 'ArrowDown') {
        downHandler()
        return true
      }

      if (event.key === 'Enter') {
        enterHandler(event)
        return true
      }

      return false
    },
  }))

  return (
    <div className="dropdown-menu">
      {props.items.length
        ? props.items.map((item, index) => (
          <button
            className={index === selectedIndex ? 'is-selected' : ''}
            key={index}
            onClick={() => selectItem(index)}
          >
            {item}
          </button>
        ))
        : <div className="item">No result</div>
      }
    </div>
  )
})

Dropdown.displayName = 'Dropdown'

export default Dropdown