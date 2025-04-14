from functions import create_driver, read_product_from_excel, google_search_selenium
from functions import get_torob_info, find_best_link_torob, write_to_json_file
from functions import convert_json_to_excel, sort_result_google_by_similarity

def main():
    driver = create_driver()

    result_torob = {}
    result_google = {}

    products = read_product_from_excel("excel/monitor.xlsx")

    for product in products:
        query = f"خرید و قیمت {product} ترب"
        links_torob = google_search_selenium(driver, query, product)
        if links_torob is None: print("links_torob is none!")
        result_google[product] = links_torob
        print(f"working on {product}\n" + 80 * "=")
        write_to_json_file(result_google, "output/output_result_google.json")
        torob_infos = {}
        for result_index, (pname, percent, link) in enumerate(links_torob, start=1):
            torob_info = get_torob_info(link, product)
            if torob_info == "error":
                error_product = {product: link}
                print("get torob info func have an error")
                write_to_json_file(error_product, "output/output_error_product.json")
            elif torob_info == "no seller": continue
            else:
                print("found an info for ", product)
                torob_info = {i+"R"+str(result_index): j for i, j in torob_info.items() if j['price'] != "N/A" and j['price'] != "0"}
                torob_infos.update(torob_info)
                if len(torob_infos) >= 4: break
        torob_infos = dict(sorted(torob_infos.items(), key=lambda item: int(item[1]['price'])))
        torob_infos = {key+"_"+str(ind): value for ind, (key, value) in enumerate(torob_infos.items())}
        if len(torob_infos)==0:
            no_seller_product = {product: link}
            print("get torob info func don't find any seller")
            write_to_json_file(no_seller_product, "output/output_no_seller.json")
        elif len(torob_infos) < 4:
            for i in range(len(torob_infos)-4):
                torob_infos.update({
                    f"{product}_0": {"link": "N/A", "price": "N/A", "name": "N/A"}
                })
        elif len(torob_infos) > 4:
            torob_infos = dict(list(torob_infos.items())[:4])
        torob_infos = {product: torob_infos}
        write_to_json_file(torob_infos, "output/output_torob.json")

if __name__ == "__main__":
    main()
    convert_json_to_excel("excel/output_crucial.xlsx")
    #sort_result_google_by_similarity()
