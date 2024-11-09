def recursively_loop_collection(top_collection, check_object, what_to_do, levels=10):
    def recurse(looped_item, depth):
        if depth > levels:
            print("at limit")
            return

        item_is_collection = hasattr(looped_item, "objects")

        if item_is_collection:
            # loop collection items
            for child in looped_item.objects:
                recurse(child, depth + 1)
            # loop other collections?
            for child in looped_item.children:
                recurse(child, depth + 1)
        else:
            if check_object(looped_item):
                what_to_do(looped_item)
            # loop object children
            for child in looped_item.children:
                recurse(child, depth + 1)

    recurse(top_collection, 0)
