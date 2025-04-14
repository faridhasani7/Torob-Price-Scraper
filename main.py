from functions import (
    create_driver, read_product_from_excel, google_search_selenium,
    get_torob_info, write_to_json_file, convert_json_to_excel
)

def main():
    """
    Main function to create driver, search products on Google,
    extract Torob information, and write results to JSON files.
    """
    driver = create_driver()
    result_torob = {}
    result_google = {}

    # Read product names from Excel file
    products = read_product_from_excel("data/excel/monitor.xlsx")

    for product in products:
        query = f"خرید و قیمت {product} ترب"
        links_torob = google_search_selenium(driver, query, product)
        
        if links_torob is None:
            print("links_torob is None!")
        
        result_google[product] = links_torob
        print(f"Working on {product}\n" + "=" * 80)
        write_to_json_file(result_google, "data/output/output_result_google.json")
        torob_infos = {}
        
        for result_index, (pname, percent, link) in enumerate(links_torob, start=1):
            torob_info = get_torob_info(link, product)
            if torob_info == "error":
                error_product = {product: link}
                print("Error in get_torob_info function for product:", product)
                write_to_json_file(error_product, "data/output/output_error_product.json")
            elif torob_info == "no seller":
                continue
            else:
                print("Found info for", product)
                # Filter out offers with invalid price
                torob_info = {
                    i + "R" + str(result_index): j 
                    for i, j in torob_info.items() 
                    if j['price'] != "N/A" and j['price'] != "0"
                }
                torob_infos.update(torob_info)
                if len(torob_infos) >= 4:
                    break
        
        # Sort sellers by price and adjust keys
        torob_infos = dict(sorted(torob_infos.items(), key=lambda item: int(item[1]['price'])))
        torob_infos = {key + "_" + str(ind): value for ind, (key, value) in enumerate(torob_infos.items())}
        
        # In case there are less than 4 sellers, add dummy entries
        if len(torob_infos) == 0:
            no_seller_product = {product: link}
            print("No seller found for", product)
            write_to_json_file(no_seller_product, "data/output/output_no_seller.json")
        elif len(torob_infos) < 4:
            for i in range(4 - len(torob_infos)):
                torob_infos.update({
                    f"{product}_fake_{i}": {"link": "N/A", "price": "N/A", "name": "N/A"}
                })
        elif len(torob_infos) > 4:
            torob_infos = dict(list(torob_infos.items())[:4])
        
        torob_infos = {product: torob_infos}
        write_to_json_file(torob_infos, "data/output/output_torob.json")

if __name__ == "__main__":
    main()
    convert_json_to_excel("data/excel/output_crucial.xlsx")
